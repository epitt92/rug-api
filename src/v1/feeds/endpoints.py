from fastapi import APIRouter
import random, json, boto3, os, dotenv, pandas as pd

from src.v1.feeds.schemas import FeedResponse
from src.v1.shared.schemas import Token, ScoreResponse, Score, Chain
from src.v1.shared.constants import ETHEREUM_CHAIN_ID

dotenv.load_dotenv()

tokens = None
with open('src/v1/shared/files/tokens.json') as f:
    tokens = json.load(f).get("tokens")

token_list = list(map(lambda s: s.lower(), tokens.keys()))
token_scores = {}

client = boto3.client(
    'timestream-query',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="eu-west-1"
)

for token in token_list:
    dummyScore = ScoreResponse(
                overallScore=float(random.uniform(0, 100)), 
                liquidityScore=Score(value=float(random.uniform(0, 100)), description="No liquidity description available."), 
                transferrabilityScore=Score(value=float(random.uniform(0, 100)), description="No transferrability description available."), 
                supplyScore=Score(value=float(random.uniform(0, 100)), description="No supply description available.")
            )
    
    token_scores[token] = dummyScore

ETHEREUM = Chain(chainId=ETHEREUM_CHAIN_ID)

router = APIRouter()

async def get_response(limit: int = 10):
    output_tokens = random.sample(token_list, limit)

    response = []

    for token in output_tokens:
        dictionaryItem = tokens.get(token)
        dictionaryResult = {
            "name": dictionaryItem.get("name"),
            "symbol": dictionaryItem.get("symbol"),
            "tokenAddress": token,
            "decimals": dictionaryItem.get("decimals"),
            "logoUrl": dictionaryItem.get("logoUrl"),
            "score": token_scores.get(token),
            "chain": ETHEREUM
        }

        response.append(Token(**dictionaryResult))

    return FeedResponse(items=response)

@router.get("/hot", response_model=FeedResponse)
async def get_hot_tokens(limit: int = 10):
    return await get_response(limit)


@router.get("/new", response_model=FeedResponse)
async def get_new_tokens(limit: int = 10):
    return await get_response(limit)


@router.get("/featured", response_model=FeedResponse)
async def get_featured_tokens(limit : int = 10):
    return await get_response(limit)


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

    response = client.query(QueryString=query)

    processed_rows = [process_row(row) for row in response["Rows"]]

    # Handle the data as a pandas dataframe to pivot the data
    df = pd.DataFrame(processed_rows).drop(['time', 'address', 'blockchain', 'timestamp'], axis=1)
    pdf = df.pivot(index='eventHash', columns='measureName', values='value')

    # Return the data as a list of dictionaries
    return pdf.to_dict('records')
