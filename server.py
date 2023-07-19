from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse

import v1

TITLE = 'rug.ai API'
VERSION = 1.9

DESCRIPTION = f"""
### Token Endpoints

This router, included under the `/token` prefix, handles general endpoints related to the token itself.

It provides APIs for querying the token name and symbol, the total supply, or other token-related functionalities. It also provides APIs for querying social media links and other metadata, alongside modifying the token metadata in storage.

### Search Endpoints

This router, included under the `/search` prefix, handles endpoints related to search functionalities.

It provides APIs for searching and retrieving data from platform storage, such as search by keywords, filtering options, or advanced search criteria.

### Token Reel Endpoints

This router, included under the `/tokens` prefix, handles endpoints related to the token reel.

It provides APIs for retrieving the token reel, which is a list of tokens that are currently trending on the platform.

### Chart Endpoints

This router, included under the `/chart` prefix, handles endpoints related to the token chart.
"""

def custom_schema():
    openapi_schema = get_openapi(
        title=TITLE,
        version=VERSION,
        description=DESCRIPTION,
        routes=app.routes
    )

    openapi_schema["info"] = {
        "title": TITLE,
        "version": VERSION,
        "description": DESCRIPTION,
    }

    app.openapi_schema = openapi_schema

    return app.openapi_schema

app = FastAPI(docs_url="/endpoints", redoc_url="/documentation", title=TITLE, favicon='https://rug.ai/favicon.ico')

app.openapi = custom_schema

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1.v1_router)

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')


@app.get("/")
async def root():
    return {"message": "rug-api"}
