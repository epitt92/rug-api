from fastapi import APIRouter
import random, json, boto3, os, dotenv, pandas as pd, logging, time, ast
from botocore.exceptions import ClientError
from decimal import Decimal

from src.v1.feeds.constants import TOP_EVENTS_STALENESS_THRESHOLD, TOP_EVENTS_LIMIT, MOST_VIEWED_TOKENS_STALENESS_THRESHOLD, MOST_VIEWED_TOKENS_LIMIT
from src.v1.feeds.schemas import FeedResponse, Token
from src.v1.feeds.dependencies import process_row, TimestreamEventAdapter
from src.v1.shared.models import ChainEnum
from src.v1.shared.DAO import DAO
from src.v1.tokens.endpoints import get_token_metrics, get_score_info
from src.v1.shared.models import validate_token_address
from src.v1.shared.dependencies import get_token_contract_details, get_chain

dotenv.load_dotenv()

read_client = boto3.client(
    'timestream-query',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="eu-west-1"
)

write_client = TimestreamEventAdapter()

router = APIRouter()

# DynamoDB Access Object
FEEDS_DAO = DAO("feeds")

@router.post("/eventclick")
async def post_event_click(eventHash: str, userId: str):
    data = {'eventHash': eventHash, 'userId': userId}
    write_client.post(table_name='eventlogs', message=data)
    return {"message": f"Event view for {eventHash} recorded."}


@router.post("/tokenview")
async def post_token_view(chain: ChainEnum, tokenAddress: str, userId: str):
    validate_token_address(tokenAddress)
    _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)
    data = {'chain': _chain, 'token_address': tokenAddress.lower(), 'userId': userId}
    write_client.post(table_name='reviewlogs', message=data)
    return {"message": f"Token view for token {tokenAddress} on chain {chain} recorded."}


@router.get("/mostviewed")
async def get_most_viewed_tokens(limit: int = 50, numMinutes: int = 60):
    # Add a DAO check for both supply and transferrability summary
    _most_viewed_tokens = FEEDS_DAO.find_most_recent_by_pk("mostviewed")
    
    logging.info(f'Fetching most viewed tokens with limit {limit} and numMinutes {numMinutes}...')

    current_time, found = int(time.time()), False

    if _most_viewed_tokens:
        # Check the timestamp on the most recent saved value
        timestamp = _most_viewed_tokens.get('timestamp')

        # If the timestamp exists in the response, check whether it is valid
        if timestamp:
            value = _most_viewed_tokens.get('value')
            # If the timestamp is less than an hour old, return the cached value
            if value and (current_time - timestamp < MOST_VIEWED_TOKENS_STALENESS_THRESHOLD):
                if len(value) < MOST_VIEWED_TOKENS_LIMIT:
                    found = False
                else:
                    found = True
                    # Parsing the dictionary objects from the DAO result
                    output = _most_viewed_tokens.get('value')
                    for idx, item in enumerate(output):
                        if item.get('chain'):
                            try:
                                if isinstance(item.get('chain'), str):
                                    output[idx]['chain'] = json.loads(item['chain'])
                                elif isinstance(item.get('chain'), dict):
                                    output[idx]['chain'] = item.get('chain')
                                else:
                                    logging.error(f'Chain was an unexpected type: {type(item.get("chain"))}')
                                    output[idx]['chain'] = None
                            except Exception as e:
                                logging.error(f'An exception occurred whilst parsing the chain info {item.get("chain")}: {e}')
                                output[idx]['chain'] = None
                                
                        if item.get('score'):
                            try:
                                if isinstance(item.get('score'), str):
                                    output[idx]['score'] = json.loads(item['score'])
                                elif isinstance(item.get('score'), dict):
                                    output[idx]['score'] = item.get('score')
                                else:
                                    logging.error(f'Score was an unexpected type: {type(item.get("score"))}')
                                    output[idx]['score'] = None
                            except Exception as e:
                                logging.error(f'An exception occurred whilst parsing the score info {item.get("score")}: {e}')
                                output[idx]['score'] = None
        
                    return output
            found = False

    output = None

    if not found:
        logging.info(f'No cached value found for most viewed tokens. Calculating from scratch...')
        output = await get_most_viewed_token_result(limit, numMinutes)

        logging.info(f'Length of calculated most viewed tokens: {len(output)}')
        if not output:
            return []
        
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
            
        output = convert_floats_to_decimals(output)
        
        # Write the output to the DAO if it has sufficient length
        if len(output) > MOST_VIEWED_TOKENS_LIMIT:
            try:
                logging.info(f'Writing most viewed tokens to DAO...')
                FEEDS_DAO.insert_one(partition_key_value="mostviewed", item={'timestamp': int(time.time()), 'value': output})
            except ClientError as e:
                logging.warning(f'An unknown boto3 exception occurred while writing most viewed tokens to DAO: {e}')
                return []
            except Exception as e:
                logging.warning(f'An unknown exception occurred while writing most viewed tokens to DAO: {e}')
                return []
            
    return output if output else []


async def get_most_viewed_token_result(limit: int = 10, numMinutes: int = 30):
    # Fetch (chain, tokenAddress) pairs for most viewed tokens
    if limit > 100:
        limit = 100

    # Query to calculate the most viewed tokens in the past numMinutes minutes
    query = f'''
        SELECT "chain", "token_address", COUNT("token_address") as "count"
        FROM "rug_api_db"."reviewlogs" AS te
        WHERE time between ago({numMinutes}m) and now()
        GROUP BY "chain", "token_address"
        ORDER BY "count" DESC
        LIMIT {limit}
        '''

    response = read_client.query(QueryString=query)

    def process_row(row):
        try:
            chain = row['Data'][0]['ScalarValue']
            tokenAddress = row['Data'][1]['ScalarValue']
            count = int(row['Data'][2]['ScalarValue'])
        except Exception as e:
            logging.error(f'An exception occurred whilst processing the row: {row}.\n\n Exception: {e}')
            return None
        
        try:
            validate_token_address(tokenAddress)
        except Exception as e:
            logging.error(f'An exception occurred whilst validating the token address {tokenAddress} on chain {chain}: {e}')
            return None

        return {
            'chain': row['Data'][0]['ScalarValue'],
            'tokenAddress': row['Data'][1]['ScalarValue'],
            'count': int(row['Data'][2]['ScalarValue'])
        }

    result = [process_row(row) for row in response["Rows"]]

    # Filter out process entries for which an exception occurred
    result = [row for row in result if row]
    
    output = []
    for item in result:
        if item.get('tokenAddress') and item.get('chain'):
            logging.info(f'Fetching token details for token {item.get("tokenAddress")} on chain {item.get("chain")}...')
            try:
                token_contract_info = await get_token_details(item.get('chain'), item.get('tokenAddress'))
            except Exception as e:
                logging.error(f'An exception occurred whilst fetching token details for token {item.get("tokenAddress")} on chain {item.get("chain")}: {e}')
                continue

            logging.info(f'Token name and symbol identified as {token_contract_info.get("name")} ({token_contract_info.get("symbol")})')

            try:
                score_info = await get_score_info(eval(f"ChainEnum.{item.get('chain')}"), item.get('tokenAddress'))
            except Exception as e:
                logging.error(f'An exception occurred whilst fetching score info for token {item.get("tokenAddress")} on chain {item.get("chain")}: {e}')
                score_info = None

            chain_ = get_chain(item.get('chain')).json()
            score_ = score_info.json() if score_info else None

            if chain_:
                try:
                    if isinstance(chain_, str):
                        chain_ = json.loads(chain_)
                    elif isinstance(chain_, dict):
                        chain_ = chain_
                    else:
                        logging.error(f'Chain was an unexpected type: {type(chain_)}')
                        chain_ = None
                except Exception as e:
                    logging.error(f'An exception occurred whilst parsing the chain info for token {item.get("tokenAddress")} on chain {item.get("chain")}: {e}')
                    chain_ = None

            if score_:
                try:
                    if isinstance(score_, str):
                        score_ = json.loads(score_)
                    elif isinstance(score_, dict):
                        score_ = score_
                    else:
                        logging.error(f'Score was an unexpected type: {type(score_)}')
                        score_ = None
                except Exception as e:
                    logging.error(f'An exception occurred whilst parsing the score info for token {item.get("tokenAddress")} on chain {item.get("chain")}: {e}')
                    score_ = None

            output.append({
                'name': token_contract_info.get('name'),
                'symbol': token_contract_info.get('symbol'),
                'tokenAddress': item.get('tokenAddress'),
                'chain': chain_,
                'score': score_})

    return output


@router.get("/topevents")
async def get_top_events(limit: int = 50, numMinutes: int = 60):
    # Add a DAO check for both supply and transferrability summary
    _top_events = FEEDS_DAO.find_most_recent_by_pk("topevents")
    
    logging.info(f'Fetching most viewed tokens with limit {limit} and numMinutes {numMinutes}...')

    current_time, found = int(time.time()), False

    if _top_events:
        # Check the timestamp on the most recent saved value
        timestamp = _top_events.get('timestamp')

        # If the timestamp exists in the response, check whether it is valid
        if timestamp:
            value = _top_events.get('value')
            # If the timestamp is less than an hour old, return the cached value
            if value and (current_time - timestamp < TOP_EVENTS_STALENESS_THRESHOLD):
                if len(value) < TOP_EVENTS_LIMIT:
                    found = False
                else:
                    found = True
                    # Parsing the dictionary objects from the DAO result
                    output = _top_events.get('value')
                    # for idx, item in enumerate(output):
                    #     if item.get('chain'):
                    #         output[idx]['chain'] = json.loads(item['chain'])
                    #     if item.get('score'):
                    #         output[idx]['score'] = json.loads(item['score'])
        
                    return output
            found = False

    output = None

    if not found:
        logging.info(f'No cached value found for top events. Calculating from scratch...')
        output = await get_most_viewed_events_result(limit, numMinutes)

        logging.info(f'Length of calculated top events: {len(output)}')
        if not output:
            return []
        
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
            
        output = convert_floats_to_decimals(output)
        
        # Write the output to the DAO if it has sufficient length
        if len(output) > TOP_EVENTS_LIMIT:
            try:
                logging.info(f'Writing top events to DAO...')
                FEEDS_DAO.insert_one(partition_key_value="topevents", item={'timestamp': int(time.time()), 'value': output})
            except ClientError as e:
                logging.warning(f'An unknown boto3 exception occurred while writing top events to DAO: {e}')
                return []
            except Exception as e:
                logging.warning(f'An unknown exception occurred while writing top events to DAO: {e}')
                return []
            
    return output if output else []


async def get_most_viewed_events_result(limit: int = 10, numMinutes: int = 30):
    # Fetch (chain, tokenAddress) pairs for most viewed tokens
    if limit > 100:
        limit = 100

    # Query to calculate the most viewed tokens in the past numMinutes minutes
    query = f'''
        SELECT "eventHash", COUNT("eventHash") as "count"
        FROM "rug_api_db"."eventlogs" AS te
        WHERE time between ago({numMinutes}m) and now()
        GROUP BY "eventHash"
        ORDER BY "count" DESC
        LIMIT {limit}
        '''

    try:
        response = read_client.query(QueryString=query)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            logging.warning(f'An exception occurred whilst querying the database due to a validation error: {e}')
            logging.warning(f'The query used was: {query}')
            return []
        
    logging.info(f'Length of response: {len(response["Rows"])}')

    def process_row(row):
        try:
            return {
                'eventHash': row['Data'][0]['ScalarValue'],
                'count': int(row['Data'][1]['ScalarValue'])
            }
        except Exception as e:
            logging.error(f'process_row(row) error: {e}')
            return

    result = [process_row(row).get('eventHash') for row in response["Rows"]]
    result = [row for row in result if row]

    logging.info(f'Length of result: {len(result)}')

    if len(result) == 0:
        return []
    
    query = f'''
        SELECT te.*
        FROM "rug_feed_db"."tokenevents" AS te
        WHERE te.eventHash IN ({','.join([f"'{item}'" for item in result])})
    '''
    
    try:
        response = read_client.query(QueryString=query)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ValidationException':
            logging.warning(f'An exception occurred whilst querying the database due to a validation error: {e}')
            logging.warning(f'The query used was: {query}')
            return []

    def process_row(row):
        try:
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
        except Exception as e:
            logging.error(f'process_row(row) error: {e}')
            return
        
    logging.info(f'Length of response["Rows"]: {len(response["Rows"])}')

    processed_rows = [process_row(row) for row in response["Rows"]]
    processed_rows = [row for row in processed_rows if row]

    logging.info(f'Length of processed_rows: {len(processed_rows)}')

    if len(processed_rows) == 0:
        return []
    
    try:
        # Handle the data as a pandas dataframe to pivot the data
        df = pd.DataFrame(processed_rows).drop(['time', 'address', 'blockchain', 'timestamp'], axis=1).drop_duplicates()
        pdf = df.pivot(index='eventHash', columns='measureName', values='value')
        # Convert the timestamp to an integer
        pdf['timestamp'] = pdf['timestamp'].apply(lambda x: int(float(x)))

        output = pdf.to_dict('records')

        for idx, item in enumerate(output):
            try:
                score_info = await get_score_info(eval(f"ChainEnum.{item.get('blockchain')}"), item.get('address'))
                score_ = score_info.json() if score_info else None

                if score_:
                    try:
                        if isinstance(score_, str):
                            score_ = json.loads(score_)
                        elif isinstance(score_, dict):
                            score_ = score_
                        else:
                            logging.error(f'Score was an unexpected type: {type(score_)}')
                            score_ = None
                    except Exception as e:
                        logging.error(f'An exception occurred whilst parsing the score info for token {item.get("address")} on chain {item.get("blockchain")}: {e}')
                        score_ = None

                output[idx]['score'] = score_
            except Exception as e:
                logging.error(f'An exception occurred whilst fetching score info for token {item.get("address")} on chain {item.get("blockchain")}: {e}')
                output[idx]['score'] = None

        return output
    except KeyError as e:
        logging.error(f'A KeyError exception was thrown during the DataFrame processing step: {e}')
        return []
    except Exception as e:
        logging.error(f'An unknown exception was thrown during the DataFrame processing step: {e}')
        return []


@router.get("/tokenevents", include_in_schema=True)
async def get_token_events(number_of_events: int = 50):
    if number_of_events > 100:
        number_of_events = 100

    query = f'''
        SELECT te.*
        FROM "rug_feed_db"."tokenevents" AS te
        JOIN (
            SELECT eventHash, MAX(timestamp) AS max_timestamp
            FROM "rug_feed_db"."tokenevents"
            GROUP BY eventHash
            ORDER BY max_timestamp DESC
            LIMIT {number_of_events}
        ) AS subquery
        ON te.eventHash = subquery.eventHash AND te.timestamp = subquery.max_timestamp
        '''

    response = read_client.query(QueryString=query)

    processed_rows = [process_row(row) for row in response["Rows"]]

    # Handle the data as a pandas dataframe to pivot the data
    df = pd.DataFrame(processed_rows).drop(['time', 'address', 'blockchain', 'timestamp'], axis=1)
    pdf = df.pivot(index='eventHash', columns='measureName', values='value')

    # Convert the timestamp to an integer
    pdf['timestamp'] = pdf['timestamp'].apply(lambda x: int(float(x)))

    # Return the data as a list of dictionaries
    return pdf.to_dict('records')


@router.get('/tokendetails/{chain}/{tokenAddress}')
async def get_token_details(chain: ChainEnum, tokenAddress: str):
    tokenAddress = tokenAddress.lower()
    validate_token_address(tokenAddress)
    token_details = await get_token_contract_details(chain, tokenAddress)
    return token_details
