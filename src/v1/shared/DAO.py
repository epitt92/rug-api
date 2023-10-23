"""
Data Access Object (DAO) class to store and retrieve data from a file.
"""
import json, logging, boto3, time, redis, logging, os, dotenv
from typing import Any, Dict, List, Optional
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from json import JSONEncoder

from src.v1.shared.exceptions import SQSException

dotenv.load_dotenv()

CLIENT_URL = os.environ.get('REDIS_CLIENT_URL')
CLIENT_PORT = os.environ.get('REDIS_CLIENT_PORT')

class DecimalEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

class RAO:
    """
    Redis Access Object (RAO) class to store and retrieve data from Redis/ElastiCache.
    
    This object corresponds to a specific table name in DynamoDB. It then acts as a base layer for caching for DAO object queries.
    
    It has a TTE (Time-To-Expiry) which determines after which amount of time cached keys expire.
    
    It stores all data in a JSON-serialised string format on the Redis server.
    """
    def __init__(self, prefix: str, tte: int = 20) -> None:
        self.client_url = CLIENT_URL
        self.client_port = CLIENT_PORT
        self.prefix = prefix
        self.tte = tte # 30 minutes until keys expire
        
        if not self.client_url or not self.client_port:
            self.client = redis.Redis()
        else:
            self.client = redis.Redis(host=self.client_url, port=self.client_port, db=0)
    
    def generate_key(self, pk: str):
        return self.prefix + "_" + pk
    
    def put(self, pk: str, data: dict):
        key = self.generate_key(pk)
        logging.info(f"Storing key {key} in Redis...")
        serialised_data = json.dumps(data, cls=DecimalEncoder)
        self.client.set(key, serialised_data, ex=self.tte)
        logging.info(f"Key {key} stored in Redis...")
        return

    def get(self, pk: str):
        key = self.generate_key(pk)
        serialised_data = self.client.get(key)
        
        if not serialised_data:
            logging.info(f"Key {key} was not stored in Redis...")
            return serialised_data
        
        logging.info(f"Key {key} was stored in Redis...")
        data = json.loads(serialised_data, parse_float=float, parse_int=int)

        return data


class DAO:
    """
    Data Access Object (DAO) class to store and retrieve data from a file.
    Currently, we are using pickle to store data in a file.
    """
    def __init__(
            self,
            table_name: str,
            region_name: str = 'eu-west-2') -> None:
        """
        Initialize DAO with a collection_name.

        Args:
            table_name (str): Name of DynamoDB table
            region_name (str): Name of the region
        Raises:
            ValueError: If the partition key is not found
        """
        partition_key_name = None
        partition_range_name = None
        dynamodb = boto3.resource('dynamodb', region_name=region_name)

        self.rao = RAO(prefix=table_name)

        # Select the table
        self.table = dynamodb.Table(table_name)

        for key in self.table.key_schema:
            if key['KeyType'] == 'HASH':
                partition_key_name = key['AttributeName']
            if key['KeyType'] == 'RANGE':
                partition_range_name = key['AttributeName']
            if partition_key_name and partition_range_name:
                break

        if partition_key_name is None:
            raise ValueError(f'Could not find partition key for table {table_name}')

        self.partition_key_name = partition_key_name
        self.partition_range_name = partition_range_name

    def find_all_by_pk(
            self,
            partition_key_value: str) -> List[Dict[Any, Any]]:
        """
        Find all documents that match the partition key and its respective value.

        Args:
            partition_key_value (str): Value of the partition key

        Returns:
            List[Dict[Any, Any]]: List of matching documents
        """

        response = self.table.query(
            KeyConditionExpression=Key(self.partition_key_name).eq(partition_key_value)
        )

        return response['Items']

    def find_most_recent_by_pk(
            self,
            partition_key_value: str) -> Dict[Any, Any]:
        """
        Find the most recent document that match the partition key and its respective value.

        Args:
            partition_key_value (str): Value of the partition key

        Returns:
            List[Dict[Any, Any]]: A list containing one document if found, empty list otherwise
        """
        try:
            # Check if the key is in Redis
            data = self.rao.get(partition_key_value)
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst fetching data from Redis: {e}")
            data = None

        if data:
            logging.info(f"Key {partition_key_value} was stored in Redis...")
            return data
        
        logging.info(f"Key {partition_key_value} was not stored in Redis...")

        # If not, fetch from DynamoDB
        response = self.table.query(
            KeyConditionExpression=Key(self.partition_key_name).eq(partition_key_value),
            ScanIndexForward=False,
            Limit=1
        )

        if len(response['Items']) == 1:
            data = response['Items'][0]

            try:
                # Store in Redis
                self.rao.put(partition_key_value, data)
            except Exception as e:
                logging.error(f"Exception: An exception occurred whilst storing data in Redis: {e}")
                pass

            logging.info(f"Key {partition_key_value} was stored in Redis...")
            return data
        else:
            # Returning None here so that it's easy to do a check on whether a value exists
            return None

    def find_count_by_pk(
            self,
            partition_key_value: str) -> bool:
        """
        Find if a document exists that match the partition key and its respective value.

        Args:
            partition_key_value: Value of the partition key

        Returns:
            int: Number of documents that match the partition key and its respective value
        """
        response = self.table.query(
            KeyConditionExpression=Key(self.partition_key_name).eq(partition_key_value),
            Select='COUNT'
        )
        return response['Count']

    def insert_one(
            self,
            partition_key_value: str,
            item: Dict[Any, Any]) -> None:
        """
        Insert a document with a partition key.

        Args:
            partition_key_value (str): Value of the partition key
            item (dict): Document to be inserted
        Raises:
            ConditionalCheckFailedException: If the document already exists
        """
        item[self.partition_key_name] = partition_key_value

        logging.info(f"Inserting item {item} into DynamoDB...")
        self.table.put_item(
            Item=item,
            ConditionExpression=f'attribute_not_exists({self.partition_key_name})')
        
        try:
            # Update Redis
            self.rao.put(partition_key_value, item)
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst storing data in Redis: {e}")
            pass

    def insert_new(
        self,
        partition_key_value: str,
        item: Dict[Any, Any]) -> None:
        """
        Insert a document with a partition key.

        Args:
            partition_key_value (str): Value of the partition key
            item (dict): Document to be inserted
        """
        item[self.partition_key_name] = partition_key_value
        self.table.put_item(Item=item)

        try:
            # Update Redis
            self.rao.put(partition_key_value, item)
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst storing data in Redis: {e}")
            pass


class DatabaseQueueObject:
    """Object to interact with DynamoDB and SQS."""
    def __init__(self, table_name: str, queue_url: str, region_name: str = 'eu-west-2', staleness: Optional[int] = None) -> None:
        self.DAO = DAO(table_name=table_name, region_name=region_name)
        self.sqs = boto3.client('sqs', region_name=region_name)
        self.queue_url = queue_url
        self.staleness = staleness

    def get_item(self, pk: str, MessageGroupId: str, message_data: dict) -> Optional[dict]:
        """Try to find most recent in DynamoDB, otherwise send a message to SQS.

        To make this function work, we consider the following:
        - DynamoDB has a partition key that can be used to find the most recent item
        - The structure of the SQS message is a JSON object, therefore the input must be a serializable dict
        - We first verify if we can find the PK in DynamoDB, if not, we send a message to SQS
        - The message to SQS has the purpose of creating a new item in DynamoDB
        - While the message in SQS is not processed (by Lambda) new messages will be sent to SQS
        - Once the message is processed, the item will be created in DynamoDB
        - The additional messages in SQS will be ignored, since the item already exists in DynamoDB (however, we still
            call the Lambda function, which is not ideal) #TODO: Fix this

        Args:
            pk (str): Partition key
            MessageGroupId (str): MessageGroupId to send to SQS
            message_data (dict): Message to send to SQS

        Returns:
            Optional[dict]: If the item is found in DynamoDB, return the item, otherwise create a message
                in SQS and return None
        """
        item = self.DAO.find_most_recent_by_pk(partition_key_value=pk)

        to_queue = False

        # Check whether the item is stale or exists
        if item and item.get('timestamp'):
            if self.staleness:
                is_stale = int(time.time()) - int(item.get('timestamp')) > self.staleness
                logging.info(f'Item found is stale: {is_stale}')
                to_queue = True if is_stale else False
            
        if item is None or to_queue:
            try:
                self.sqs.send_message(
                    QueueUrl=self.queue_url,
                    MessageBody=json.dumps(message_data),
                    MessageGroupId=MessageGroupId,
                    MessageDeduplicationId=MessageGroupId
                )

                logging.info(f'Success: Message sent to SQS: {message_data}')
            except Exception as e:
                logging.error(f'Exception: An error occurred whilst sending a message to SQS: {e}')
                raise SQSException()

        return item
