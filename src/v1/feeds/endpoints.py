from fastapi import APIRouter
import random, json, boto3, os, dotenv, pandas as pd, logging
from botocore.exceptions import ClientError

from src.v1.feeds.schemas import FeedResponse, Token
from src.v1.feeds.dependencies import process_row, TimestreamEventAdapter
from src.v1.shared.models import ChainEnum
from src.v1.tokens.endpoints import get_token_metrics, get_score_info
from src.v1.shared.exceptions import validate_token_address
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

# TODO: Must add database caching for these queries as they are very expensive and likely to return identical data for all users
# What is the optimal way to cache these?

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
async def get_most_viewed_tokens(limit: int = 10, numMinutes: int = 30):
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
            logging.error(f'An exception occurred whilst processing the row with chain {chain}, tokenAddress {tokenAddress} and count {count}: {e}')
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

            output.append({
                'name': token_contract_info.get('name'),
                'symbol': token_contract_info.get('symbol'),
                'tokenAddress': item.get('tokenAddress'),
                'chain': get_chain(item.get('chain')),
                'score': score_info})

    return output


@router.get("/topevents")
async def get_most_viewed_events(limit: int = 10, numMinutes: int = 30):
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

    processed_rows = [process_row(row) for row in response["Rows"]]

    if len(processed_rows) == 0:
        return []

    try:
        # Handle the data as a pandas dataframe to pivot the data
        df = pd.DataFrame(processed_rows).drop(['time', 'address', 'blockchain', 'timestamp'], axis=1).drop_duplicates()
        pdf = df.pivot(index='eventHash', columns='measureName', values='value')
        # Convert the timestamp to an integer
        pdf['timestamp'] = pdf['timestamp'].apply(lambda x: int(float(x)))
        return pdf.to_dict('records')
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

@router.get('tokendetails/{chain}/{tokenAddress}')
async def get_token_details(chain: ChainEnum, tokenAddress: str):
    tokenAddress = tokenAddress.lower()
    validate_token_address(tokenAddress)
    token_details = await get_token_contract_details(chain, tokenAddress)
    return token_details
