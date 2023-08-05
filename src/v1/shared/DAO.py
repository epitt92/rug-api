"""
Data Access Object (DAO) class to store and retrieve data from a file.
"""

from typing import Any, Dict, List

import boto3
from boto3.dynamodb.conditions import Key


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
        response = self.table.query(
            KeyConditionExpression=Key(self.partition_key_name).eq(partition_key_value),
            ScanIndexForward=False,
            Limit=1
        )

        if len(response['Items']) == 1:
            return response['Items'][0]
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
        self.table.put_item(
            Item=item,
            ConditionExpression=f'attribute_not_exists({self.partition_key_name})')
