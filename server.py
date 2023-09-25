from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

import dotenv

from router import v1_router

from src.v1.shared.exceptions import (
                                    RugAPIException, DatabaseLoadFailureException, 
                                    DatabaseInsertFailureException, GoPlusDataException, 
                                    UnsupportedChainException, OutputValidationError, 
                                    BlockExplorerDataException, InvalidTokenAddressException
                                    )
from src.v1.chart.exceptions import CoinGeckoChartException
from src.v1.auth.exceptions import CognitoException

dotenv.load_dotenv()

TITLE = "rug.ai API"
VERSION = "2.2"

app = FastAPI(docs_url="/endpoints", redoc_url="/documentation", title=TITLE, version=VERSION, favicon='https://rug.ai/favicon.ico')
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

######################################################
#                                                    #
#                Exception Handling                  #
#                                                    #
######################################################

# Application level exception handling, this is overriden by exception handling at the lower level
# This prevents re-booting of containers and issues with performance degredation
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500, # Internal Server Error
        content={"detail": "An unexpected and uncaught exception was raised during an API call."}
    )

@app.exception_handler(CognitoException)
async def cognito_exception_handler(request, exc: CognitoException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(RugAPIException)
async def rug_api_exception_handler(request, exc: RugAPIException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(DatabaseLoadFailureException)
async def database_load_failure_exception_handler(request, exc: DatabaseLoadFailureException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(DatabaseInsertFailureException)
async def database_insert_failure_exception_handler(request, exc: DatabaseInsertFailureException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(InvalidTokenAddressException)
async def invalid_token_address_exception_handler(request, exc: InvalidTokenAddressException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(UnsupportedChainException)
async def unsupported_chain_exception_handler(request, exc: UnsupportedChainException):
    return JSONResponse(
        status_code=501,  # Not Implemented
        content={"detail": str(exc)},
    )

@app.exception_handler(OutputValidationError)
async def output_validation_error_exception_handler(request, exc: OutputValidationError):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(GoPlusDataException)
async def go_plus_data_exception_handler(request, exc: GoPlusDataException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(CoinGeckoChartException)
async def go_plus_data_exception_handler(request, exc: CoinGeckoChartException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
    )

@app.exception_handler(BlockExplorerDataException)
async def block_explorer_data_exception_handler(request, exc: BlockExplorerDataException):
    return JSONResponse(
        status_code=500,  # Internal Server Error
        content={"detail": str(exc)},
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
