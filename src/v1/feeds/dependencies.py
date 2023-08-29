import time, boto3, logging

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
                    {'Name': 'eventHash', 'Value': data.get('eventHash')},
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
        records.append(self.generate_record(dimensions, 'userId', data.get('userId')))           
        return records

    def post(self, table_name: str, message: dict):
        records = self.generate_records(table_name, message)

        try:
            response = self.client.write_records(
                DatabaseName=self.database,
                TableName=table_name,
                Records=records
            )
            _ = response["ResponseMetadata"]["HTTPStatusCode"]
        except self.client.exceptions.RejectedRecordsException as err:
            for _record in err.response["RejectedRecords"]:
                logging.error("Rejected Index " + str(_record["RecordIndex"]) + ": " + _record["Reason"])
        except Exception as e:
                logging.error(f"An unknown error occurred: {e}")
