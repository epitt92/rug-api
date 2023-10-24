import time, boto3, logging
from botocore.exceptions import BotoCoreError, ClientError
from decimal import Decimal

from src.v1.shared.constants import CHAIN_ID_MAPPING, CHAIN_SYMBOL_MAPPING
from src.v1.feeds.exceptions import TimestreamWriteException

def process_row(row):
    if row['Data'][6].get('ScalarValue') is None:
        value = row['Data'][7]['ScalarValue']
    else:
        value = row['Data'][6]['ScalarValue']

    return {
        'eventHash': row['Data'][0]['ScalarValue'],
        'address': row['Data'][1]['ScalarValue'],
        'blockchain': row['Data'][2]['ScalarValue'],
        'timestamp': row['Data'][3]['ScalarValue'],
        'measureName': row['Data'][4]['ScalarValue'],
        'time': row['Data'][5]['ScalarValue'],
        'value': value
    }


def convert_floats_to_decimals(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_floats_to_decimals(value)
        return data
    elif isinstance(data, list):
        return [convert_floats_to_decimals(item) for item in data]
    elif isinstance(data, float):
        return Decimal(str(data))
    else:
        return data


def get_swap_link(dex, network, token_address):
    SWAP_URLS = {
        'uniswapv2': f'https://app.uniswap.org/swap?chain={network}&inputCurrency={token_address}',
        'uniswapv3': f'https://app.uniswap.org/swap?chain={network}&inputCurrency={token_address}',
        'pancakeswapv2': f'https://pancakeswap.finance/swap?chain={CHAIN_SYMBOL_MAPPING[network]}&inputCurrency={token_address}',
        'pancakeswapv3': f'https://pancakeswap.finance/swap?chain={CHAIN_SYMBOL_MAPPING[network]}&inputCurrency={token_address}',
        'sushiswap': f'https://app.sushi.com/swap?chainId={CHAIN_ID_MAPPING[network]}&inputCurrency={token_address}',
        'baseswap': f'https://baseswap.fi/swap?inputCurrency={token_address}',
        'rocketswap': f'https://rocketswap.exchange/swap?chain={network}&inputCurrency={token_address}',
        'traderjoe': f'https://traderjoexyz.com/{network}/trade?inputCurrency={token_address}',
    }

    if dex not in SWAP_URLS:
        logging.error(f'Exception: Unsupported DEX {dex}')
        raise ValueError(f"Unsupported DEX: {dex}")

    return SWAP_URLS[dex]


class TimestreamEventAdapter():
    def __init__(self, database: str = "rug_api_db") -> None:
        self.database = database
        self.interval = 1

        self.client = boto3.client("timestream-write", region_name="eu-west-1")

    @staticmethod
    def get_type(value):
        if isinstance(value, str):
            return "VARCHAR"
        elif isinstance(value, float) or isinstance(value, int):
            return "DOUBLE"
        elif isinstance(value, bool):
            return "BOOLEAN"
        else:
            try:
                _ = str(value)
                return "VARCHAR"
            except:
                raise Exception(f"Measure value {value} could not be typed.")

    def generate_record_measures(self, key, value):
        return {'MeasureName': key, 'MeasureValue': str(value), 'MeasureValueType': self.get_type(value)}

    @staticmethod
    def generate_dimensions(table_name: str, data: str):
        if table_name == 'eventlogs':
            return {
                'Dimensions': [
                    {'Name': 'event_hash', 'Value': data.get('event_hash')},
                ]
            }
        elif table_name == 'reviewlogs':
            return {
                'Dimensions': [
                    {'Name': 'token_address', 'Value': data.get('token_address')},
                    {'Name': 'chain', 'Value': data.get('chain')}
                ]
            }
        else:
            raise Exception(f"Table name {table_name} not recognised.")

    def generate_record(self, dimensions, key, value):
        record = {
                **dimensions,
                **{'Time': str(int(time.time())), 'TimeUnit': 'SECONDS'}, 
                **self.generate_record_measures(key, value)
        }
        
        return record

    def generate_records(self, table_name: str, data: dict):
        dimensions = self.generate_dimensions(table_name, data)
        
        records = []
        records.append(self.generate_record(dimensions, 'user_id', data.get('user_id')))           
        return records

    def post(self, table_name: str, message: dict):
        try:
            records = self.generate_records(table_name, message)
        except Exception as e:
            message = f"Exception: An error occurred whilst generating records: {e}"
            logging.error(message)
            raise TimestreamWriteException(message=message)

        logging.info(f"Records: {records}")
        try:
            response = self.client.write_records(
                DatabaseName=self.database,
                TableName=table_name,
                Records=records
            )
            _ = response["ResponseMetadata"]["HTTPStatusCode"]
        except ClientError as e:
            # Handle specific Boto3 client errors
            if e.response['Error']['Code'] == 'ThrottlingException':
                message = f"Exception: Error code {e.response['Error']['Code']}. Request was throttled. Consider retrying the request with exponential backoff."
                logging.error(message)
                raise TimestreamWriteException(message=message)
            elif e.response['Error']['Code'] == 'ValidationException':
                message = f"Exception: Error code {e.response['Error']['Code']}. A Validation Error: {e}"
                logging.error(message)
                raise TimestreamWriteException(message=message)
            elif e.response['Error']['Code'] == 'ResourceNotFoundException':
                message = f"Exception: Error code {e.response['Error']['Code']}. The database or table does not exist."
                logging.error(message)
                raise TimestreamWriteException(message=message)
            elif e.response['Error']['Code'] == 'RejectedRecordsException':
                message = f"Exception: Error code {e.response['Error']['Code']}. Rejected records: {e}"
                rejected_records = e.response['Error']['RejectedRecords']
                for record in rejected_records:
                    logging.error(f"Record {record['RecordIndex']} was rejected due to: {record['Reason']}")
                raise TimestreamWriteException(message=message)
            else:
                # Rethrow the error if it is not one that we expected
                message = f"Exception: Error code {e.response['Error']['Code']}. An unexpected error: {e}"
                logging.error(message)
                raise TimestreamWriteException(message=message)
        except BotoCoreError as e:
            # Handle errors inherent to the core boto3 (like network issues)
            message = f"Exception: BotoCore Error: {e}"
            logging.error(message)
            raise TimestreamWriteException(message=message)
        except Exception as e:
            message = f"Exception: An unknown error occurred: {e}"
            logging.error(message)
            raise TimestreamWriteException(message=message)
