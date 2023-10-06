from fastapi import APIRouter, Depends, Cookie
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
import json, boto3, os, dotenv, pandas as pd, logging, time, ast
from botocore.exceptions import ClientError
from decimal import Decimal

from src.v1.feeds.constants import TOP_EVENTS_STALENESS_THRESHOLD, TOP_EVENTS_LIMIT, MOST_VIEWED_TOKENS_STALENESS_THRESHOLD, MOST_VIEWED_TOKENS_LIMIT, MOST_VIEWED_TOKENS_NUM_MINUTES, TOP_EVENTS_NUM_MINUTES
from src.v1.feeds.dependencies import process_row, TimestreamEventAdapter, convert_floats_to_decimals
from src.v1.feeds.models import EventClick, TokenView
from src.v1.feeds.exceptions import TimestreamReadException, TimestreamWriteException

from src.v1.shared.models import ChainEnum
from src.v1.shared.DAO import DAO
from src.v1.shared.models import validate_token_address
from src.v1.shared.dependencies import get_token_contract_details, get_chain
from src.v1.shared.exceptions import DatabaseLoadFailureException, DatabaseInsertFailureException

from src.v1.tokens.endpoints import get_score_info

from src.v1.auth.endpoints import decode_token

dotenv.load_dotenv()

read_client = boto3.client(
    'timestream-query',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="eu-west-1"
)

write_client = TimestreamEventAdapter()

router = APIRouter()

FEEDS_DAO = DAO("feeds")

@router.post("/eventclick", dependencies=[Depends(decode_token)])
async def post_event_click(eventClick: EventClick):
    # TODO: Get user ID from token

    try:
        eventHash = eventClick.event_hash
        userId = "TEMP"
    except Exception as e:
        logging.error(f'An exception occurred whilst parsing the eventClick: {eventClick}. Exception: {e}')
        return JSONResponse(status_code=400, content={"detail": f"An exception occurred whilst parsing the eventClick: {eventClick}. Exception: {e}"})

    data = {'event_hash': eventHash, 'user_id': userId}

    write_client.post(table_name='eventlogs', message=data)

    return JSONResponse(status_code=200, content={"detail": f"Event view for {eventHash} from user {userId} recorded."})


@router.post("/tokenview", dependencies=[Depends(decode_token)])
async def post_token_view(tokenView: TokenView):
    # TODO: Get user ID from token
    try:
        chain = tokenView.chain
        token_address = tokenView.token_address
        user_id = "TEMP"

        _chain = str(chain.value) if isinstance(chain, ChainEnum) else str(chain)

        data = {'chain': _chain, 'token_address': token_address, 'user_id': user_id}
    except Exception as e:
        logging.error(f'An exception occurred whilst parsing the tokenView: {tokenView}. Exception: {e}')
        return JSONResponse(status_code=400, content={"detail": f"An exception occurred whilst parsing the tokenView: {tokenView}. Exception: {e}"})

    write_client.post(table_name='reviewlogs', message=data)
    return JSONResponse(status_code=200, content={"detail": f"Token view for token {token_address} on chain {chain} from user {user_id} recorded."})


# TODO: Add more robust exception handling to this endpoint
# TODO: Remove limit and numMinutes
@router.get("/mostviewed", dependencies=[Depends(decode_token)])
async def get_most_viewed_tokens(limit: int = 50):

    # Add a DAO check for most viewed reel
    try:
        _most_viewed_tokens = FEEDS_DAO.find_most_recent_by_pk("mostviewed")
    except ClientError as e:
        logging.error(f"Exception: Boto3 exception whilst fetching data from 'feeds' with PK 'mostviewed': {e}")
        raise DatabaseLoadFailureException()
    except Exception as e:
        logging.error(f"Exception: Unknown exception whilst fetching data from 'feeds' with PK 'mostviewed': {e}")
        raise DatabaseLoadFailureException()

    logging.info(f'Fetching most viewed tokens with limit {limit}...')

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

                    for idx, item in enumerate(output[:limit]):
                        if item.get('chain'):
                            try:
                                if isinstance(item.get('chain'), str):
                                    output[idx]['chain'] = json.loads(item['chain'])
                                elif isinstance(item.get('chain'), dict):
                                    output[idx]['chain'] = item.get('chain')
                                else:
                                    logging.error(f'Chain was an unexpected type: {type(item.get("chain"))} for item {item}')
                                    output[idx]['chain'] = None
                            except Exception as e:
                                logging.error(f'An exception occurred whilst parsing the chain info {item.get("chain")} for item {item}: {e}')
                                output[idx]['chain'] = None

                        if item.get('score'):
                            try:
                                if isinstance(item.get('score'), str):
                                    output[idx]['score'] = json.loads(item['score'])
                                elif isinstance(item.get('score'), dict):
                                    output[idx]['score'] = item.get('score')
                                else:
                                    logging.error(f'Score was an unexpected type: {type(item.get("score"))} for item {item}')
                                    output[idx]['score'] = None
                            except Exception as e:
                                logging.error(f'An exception occurred whilst parsing the score info {item.get("score")} for item {item}: {e}')
                                output[idx]['score'] = None

                    return output[:limit]
            found = False

    output = None
    if not found:
        logging.info(f"No cached value found for most viewed tokens. Calculating from scratch...")
        output = await get_most_viewed_token_result(limit=50, num_minutes=MOST_VIEWED_TOKENS_NUM_MINUTES)

        logging.info(f"Length of calculated most viewed tokens: {len(output)}")

        if not output:
            logging.error(f"Exception: No output returned from `get_most_viewed_token_result`.")
            raise Exception("No output returned from `get_most_viewed_token_result` query.")

        try:
            output = convert_floats_to_decimals(output)
        except Exception as e:
            logging.error(f"Exception: An exception occurred whilst converting floats to decimals: {e}")
            raise e

        # Write the output to the DAO if it has sufficient length
        if len(output) > MOST_VIEWED_TOKENS_LIMIT:
            try:
                logging.info(f"Writing most viewed tokens to DAO...")
                FEEDS_DAO.insert_one(partition_key_value="mostviewed", item={'timestamp': int(time.time()), 'value': output})
            except ClientError as e:
                message = f"Exception: An unknown boto3 exception occurred while writing most viewed tokens to DAO: {e}"
                logging.warning(message)
                raise DatabaseInsertFailureException(message=message)
            except Exception as e:
                message = f"Exception: An unknown exception occurred while writing most viewed tokens to DAO: {e}"
                logging.warning(message)
                raise DatabaseInsertFailureException(message=message)
        else:
            logging.warning(f"The length of the output was {len(output)}, which is less than the limit of {MOST_VIEWED_TOKENS_LIMIT}.")

    return output[:limit] if output else []

# TODO: Add more robust exception handling to this endpoint
async def get_most_viewed_token_result(limit: int = 50, num_minutes: int = 30):
    # Fetch (chain, tokenAddress) pairs for most viewed tokens
    if limit > 50:
        limit = 50

    # Query to calculate the most viewed tokens in the past numMinutes minutes
    query = f'''
        SELECT "chain", "token_address", COUNT("token_address") as "count"
        FROM "rug_api_db"."reviewlogs" AS te
        WHERE time between ago({num_minutes}m) and now()
        GROUP BY "chain", "token_address"
        ORDER BY "count" DESC
        LIMIT {limit}
        '''

    response = read_client.query(QueryString=query)

    def process_row(row):
        try:
            chain = row['Data'][0]['ScalarValue']
            token_address = row['Data'][1]['ScalarValue']
            count = int(row['Data'][2]['ScalarValue'])
        except Exception as e:
            logging.error(f'An exception occurred whilst processing the row: {row}. Exception: {e}')
            return None

        validate_token_address(token_address)

        return {
            'chain': chain,
            'token_address': token_address,
            'count': count
        }

    result = [process_row(row) for row in response["Rows"]]

    # Filter out process entries for which an exception occurred
    result = [row for row in result if row]

    if len(result) == 0:
        logging.warning(f"No results returned from query: {query}")
        return []

    output = []
    for item in result:
        if item.get('token_address') and item.get('chain'):
            logging.info(f'Fetching token details for token {item.get("token_address")} on chain {item.get("chain")}...')
            try:
                token_contract_info = await get_token_details(item.get('chain'), item.get('token_address'))
            except Exception as e:
                logging.error(f'An exception occurred whilst fetching token details for token {item.get("token_address")} on chain {item.get("chain")}: {e}')
                continue

            logging.info(f'Token name and symbol identified as {token_contract_info.get("name")} ({token_contract_info.get("symbol")})')

            try:
                score_info = await get_score_info(eval(f"ChainEnum.{item.get('chain')}"), item.get('token_address'))
            except Exception as e:
                logging.error(f'An exception occurred whilst fetching score info for token {item.get("token_address")} on chain {item.get("chain")}: {e}')
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
                    logging.error(f'An exception occurred whilst parsing the chain info for token {item.get("token_address")} on chain {item.get("chain")}: {e}')
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
                    logging.error(f'An exception occurred whilst parsing the score info for token {item.get("token_address")} on chain {item.get("chain")}: {e}')
                    score_ = None

            output.append({
                'name': token_contract_info.get('name'),
                'symbol': token_contract_info.get('symbol'),
                'tokenAddress': item.get('token_address'),
                'chain': chain_,
                'score': score_})

    return output

# TODO: Add more robust exception handling to this endpoint
@router.get("/topevents", dependencies=[Depends(decode_token)])
async def get_top_events(limit: int = 50):
    logging.info(f'Fetching top event list with limit {limit}...')

    # Add a DAO check for both supply and transferrability summary
    try:
        _top_events = FEEDS_DAO.find_most_recent_by_pk("topevents")
    except ClientError as e:
        logging.error(f"Exception: Boto3 exception whilst fetching data from 'feeds' with PK 'topevents': {e}")
        raise DatabaseLoadFailureException()
    except Exception as e:
        logging.error(f"Exception: Unknown exception whilst fetching data from 'feeds' with PK 'topevents': {e}")
        raise DatabaseLoadFailureException()

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

                    if not output:
                        logging.warning(f'No output returned from DAO for top events.')

                    return output[:limit] if output else []
            found = False

    output = None

    if not found:
        logging.info(f'No cached value found for top events. Calculating from scratch...')
        output = await get_most_viewed_events_result(limit=50, numMinutes=TOP_EVENTS_NUM_MINUTES)

        logging.info(f'Length of calculated top events: {len(output)}')
        if not output:
            logging.error(f'No output returned from `get_most_viewed_events_result`.')
            return []

        output = convert_floats_to_decimals(output)

        # Write the output to the DAO if it has sufficient length
        if len(output) > TOP_EVENTS_LIMIT:
            try:
                logging.info(f'Writing top events to DAO...')
                FEEDS_DAO.insert_one(partition_key_value="topevents", item={'timestamp': int(time.time()), 'value': output})
            except ClientError as e:
                logging.warning(f'An unknown boto3 exception occurred while writing top events to DAO: {e}')
                raise DatabaseInsertFailureException()
            except Exception as e:
                logging.warning(f'An unknown exception occurred while writing top events to DAO: {e}')
                raise DatabaseInsertFailureException()

    return output[:limit] if output else []

# TODO: Add more robust exception handling to this endpoint
async def get_most_viewed_events_result(limit: int = 50, numMinutes: int = 30):
    # Fetch (chain, tokenAddress) pairs for most viewed tokens
    if limit > 50:
        limit = 50

    # Query to calculate the most viewed tokens in the past numMinutes minutes
    query = f'''
        SELECT "event_hash", COUNT("event_hash") as "count"
        FROM "rug_api_db"."eventlogs" AS te
        WHERE time between ago({numMinutes}m) and now()
        GROUP BY "event_hash"
        ORDER BY "count" DESC
        LIMIT {limit}
        '''

    try:
        response = read_client.query(QueryString=query)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException':
            message = f"Request was throttled. Consider retrying with exponential backoff."
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'ValidationException':
            message = f"A validation error occurred during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            message = f"Resource not found during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            message = f"Access denied during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        else:
            message = f"An unknown exception occurred during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
    except Exception as e:
        message = f"An unknown exception occurred during call to read from Timestream: {e}"
        logging.error(message)
        raise TimestreamReadException(message=message)

    logging.info(f'Response fetched successfully! Length of response: {len(response["Rows"])}.')

    def process_row(row):
        try:
            return {
                'event_hash': row['Data'][0]['ScalarValue'],
                'count': int(row['Data'][1]['ScalarValue'])
            }
        except Exception as e:
            logging.error(f'process_row(row) error: {e}')
            logging.error(f"row: {row}")
            return

    # Highly robust, very optimised filtering for invalid rows
    result = [process_row(row)for row in response["Rows"]]
    result = [row.get('event_hash') for row in result if row]
    result = [item for item in result if item]

    logging.info(f'Success! Processed result length: {len(result)}')

    if len(result) == 0:
        logging.warning(f"No results returned from query: {query}")
        return []

    query = f'''
        SELECT te.*
        FROM "rug_feed_db"."tokenevents" AS te
        WHERE te.eventHash IN ({','.join([f"'{item}'" for item in result])})
    '''

    logging.info(f"Event hashes in result list: {result}")

    try:
        response = read_client.query(QueryString=query)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException':
            message = f"Request was throttled. Consider retrying with exponential backoff."
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'ValidationException':
            message = f"A validation error occurred during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            message = f"Resource not found during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            message = f"Access denied during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        else:
            message = f"An unknown exception occurred during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
    except Exception as e:
        message = f"An unknown exception occurred during call to read from Timestream: {e}"
        logging.error(message)
        raise TimestreamReadException(message=message)

    def process_row(row):
        try:
            if row['Data'][6].get('ScalarValue') is None:
                value = row['Data'][7]['ScalarValue']
            else:
                value = row['Data'][6]['ScalarValue']

            return {
                'event_hash': row['Data'][0]['ScalarValue'],
                'address': row['Data'][1]['ScalarValue'],
                'blockchain': row['Data'][2]['ScalarValue'],
                'timestamp': row['Data'][3]['ScalarValue'],
                'measure_name': row['Data'][4]['ScalarValue'],
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
        pdf = df.pivot(index='event_hash', columns='measure_name', values='value')
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

# TODO: Add caching to this endpoint to reduce the number of calls to Timestream
@router.get("/tokenevents",  dependencies=[Depends(decode_token)], include_in_schema=True)
async def get_token_events(number_of_events: int = 50, chain: ChainEnum = None):
    if number_of_events > 50:
        number_of_events = 50

    where_clause = f"WHERE blockchain = '{chain.value}' AND eventHash IS NOT NULL" if chain else "WHERE eventHash IS NOT NULL"

    query = f'''
        SELECT te.*
        FROM "rug_feed_db"."tokenevents" AS te
        JOIN (
            SELECT eventHash, MAX(timestamp) AS max_timestamp
            FROM "rug_feed_db"."tokenevents"
            {where_clause}
            GROUP BY eventHash
            ORDER BY max_timestamp DESC
            LIMIT {number_of_events}
        ) AS subquery
        ON te.eventHash = subquery.eventHash AND te.timestamp = subquery.max_timestamp
        '''

    try:
        response = read_client.query(QueryString=query)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ThrottlingException':
            message = f"Request was throttled. Consider retrying with exponential backoff."
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'ValidationException':
            message = f"A validation error occurred during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            message = f"Resource not found during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            message = f"Access denied during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
        else:
            message = f"An unknown exception occurred during call to read from Timestream: {e}"
            logging.error(message)
            raise TimestreamReadException(message=message)
    except Exception as e:
        message = f"An unknown exception occurred during call to read from Timestream: {e}"
        logging.error(message)
        raise TimestreamReadException(message=message)

    processed_rows = [process_row(row) for row in response["Rows"]]

    # Handle the data as a pandas dataframe to pivot the data
    df = pd.DataFrame(processed_rows).drop(['time', 'address', 'blockchain', 'timestamp'], axis=1)
    pdf = df.pivot(index='eventHash', columns='measureName', values='value')

    # Convert the timestamp to an integer
    pdf['timestamp'] = pdf['timestamp'].apply(lambda x: int(float(x)))

    # Return the data as a list of dictionaries
    return pdf.to_dict('records')

# TODO: Add more robust exception handling to this endpoint
async def get_token_details(chain: ChainEnum, token_address: str):
    token_address = token_address.lower()
    validate_token_address(token_address)

    try:
        token_details = await get_token_contract_details(chain, token_address)
    except Exception as e:
        logging.warning(f'An exception occurred whilst fetching token details for token {token_address} on chain {chain}: {e}')
        raise e

    return token_details
