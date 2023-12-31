from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError

import dotenv, logging
from apscheduler.schedulers.background import BackgroundScheduler
import time, logging

from src.utils.gcs import GCSAdapter
from src.v1.feeds.constants import *
from router import v1_router

from src.v1.shared.dependencies import load_access_token

from src.v1.shared.exceptions import (
                                    RugAPIException, DatabaseLoadFailureException,
                                    DatabaseInsertFailureException, GoPlusDataException,
                                    UnsupportedChainException, OutputValidationError,
                                    BlockExplorerDataException, InvalidTokenAddressException,
                                    RPCProviderException, SQSException
                                    )
from src.v1.chart.exceptions import CoinGeckoChartException
from src.v1.auth.exceptions import CognitoException
from src.v1.feeds.exceptions import TimestreamWriteException, TimestreamReadException

dotenv.load_dotenv()

logging.getLogger().setLevel(logging.INFO)

# Load GoPlus access token file on startup
logging.info(f"Loading GoPlus access token file on startup...")
load_access_token()
logging.info(f"GoPlus access token file loaded successfully.")

TITLE = "rug.ai API"
VERSION = "2.5"

app = FastAPI(docs_url="/endpoints", redoc_url="/documentation", title=TITLE, version=VERSION, favicon='https://rug.ai/favicon.ico')

######################################################
#                                                    #
#                Exception Handling                  #
#                                                    #
######################################################

@app.exception_handler(CognitoException)
async def cognito_exception_handler(request, exc: CognitoException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(SQSException)
async def sqs_exception_handler(request, exc: SQSException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(RequestValidationError)
async def invalid_event_hash_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,  # Internal Server Error
        content={"status_code": 400, "detail": str(exc)},
    )

@app.exception_handler(RPCProviderException)
async def rpc_provider_exception_handler(request, exc: RPCProviderException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(RugAPIException)
async def rug_api_exception_handler(request, exc: RugAPIException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(DatabaseLoadFailureException)
async def database_load_failure_exception_handler(request, exc: DatabaseLoadFailureException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(DatabaseInsertFailureException)
async def database_insert_failure_exception_handler(request, exc: DatabaseInsertFailureException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(TimestreamWriteException)
async def timestream_write_exception_handler(request, exc: TimestreamWriteException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(TimestreamReadException)
async def timestream_read_exception_handler(request, exc: TimestreamReadException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(InvalidTokenAddressException)
async def invalid_token_address_exception_handler(request, exc: InvalidTokenAddressException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(UnsupportedChainException)
async def unsupported_chain_exception_handler(request, exc: UnsupportedChainException):
    return JSONResponse(
        status_code=501,  # Not Implemented
        content={"status_code": 501, "detail": str(exc)},
    )

@app.exception_handler(OutputValidationError)
async def output_validation_error_exception_handler(request, exc: OutputValidationError):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(GoPlusDataException)
async def go_plus_data_exception_handler(request, exc: GoPlusDataException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(CoinGeckoChartException)
async def coingecko_chart_exception_handler(request, exc: CoinGeckoChartException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(BlockExplorerDataException)
async def block_explorer_data_exception_handler(request, exc: BlockExplorerDataException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"status_code": 500, "detail": str(exc)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status_code": exc.status_code, "detail": exc.detail}
    )

# Application level exception handling, this is overriden by exception handling at the lower level
# This prevents re-booting of containers and issues with performance degredation
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, # Internal Server Error
        content={"status_code": 500, "detail": "An unexpected and uncaught exception was raised during an API call."}
    )

######################################################
#                                                    #
#                 Root and Favicon                   #
#                                                    #
######################################################

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        status_code=200,
        content={"detail": "rug-api"}
    )

app.include_router(v1_router)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


# bucket = S3Adapter()
bucket = GCSAdapter()

# Cronjob updates the token JSON every 5 minutes
def cron_update_data():
    logging.info("Running cronjob to update data")
    start_time = time.time()
    networks = ["ethereum", "base"]
    for network in networks:
        pools = bucket.get(f"pools/{network}/pools.json")
        pools_ = pools[::-1]

        for pool in pools_:
            token0 = pool["token0"].lower()
            token1 = pool["token1"].lower()

            if not POOL_INDEXER[network].get(token0):
                POOL_INDEXER[network][token0] = [pool]
            else:
                POOL_INDEXER[network][token0].append(pool)

            if not POOL_INDEXER[network].get(token1):
                POOL_INDEXER[network][token1] = [pool]
            else:
                POOL_INDEXER[network][token1].append(pool)

        for key in POOL_INDEXER[network].keys():
            pools_list = POOL_INDEXER[network][key]
            POOL_INDEXER[network][key] = list(
                {v["address"]: v for v in pools_list}.values()
            )

    logging.warning(f"Pool indexer job is finished in {time.time() - start_time}")

# Load latest data on startup
cron_update_data()

# Background scheduler to run cronjob to update data
scheduler = BackgroundScheduler()
scheduler.add_job(cron_update_data, "interval", minutes=5)
scheduler.start()
