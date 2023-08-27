from fastapi import APIRouter
import random, json, boto3, os, dotenv, pandas as pd

from src.v1.feeds.schemas import FeedResponse
from src.v1.feeds.dependencies import process_row
from src.v1.shared.models import ChainEnum

dotenv.load_dotenv()

client = boto3.client(
    'timestream-query',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="eu-west-1"
)

# TODO: Implement a timestream-write client also

router = APIRouter()


@router.post("/eventclick")
async def post_event_click(eventHash: str):
    # TODO: Implement this function

    # Create a new row for the timestream database

    # Write the row to the database

    return {"message": "Event view recorded."}


@router.post("/tokenview")
async def post_token_view(chain: ChainEnum, tokenAddress: str):
    # TODO: Implement this function

    # Create a new row for the timestream database

    # Write the row to the database

    return {"message": "Token view recorded."}


@router.get("/mostviewed", response_model=FeedResponse)
async def get_most_viewed_tokens(limit: int = 10):
    # TODO: Implement this function

    # Fetch (chain, token_address) pairs for most viewed tokens

    # Fetch token data from the database for scores

    # Return the data as a list of dictionaries

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

    response = client.query(QueryString=query)

    processed_rows = [process_row(row) for row in response["Rows"]]

    # Handle the data as a pandas dataframe to pivot the data
    df = pd.DataFrame(processed_rows).drop(['time', 'address', 'blockchain', 'timestamp'], axis=1)
    pdf = df.pivot(index='eventHash', columns='measureName', values='value')

    # Convert the timestamp to an integer
    pdf['timestamp'] = pdf['timestamp'].apply(lambda x: int(float(x)))

    # Return the data as a list of dictionaries
    return pdf.to_dict('records')
