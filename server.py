from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse

import v1

TITLE = 'rug.ai API'
VERSION = 1.8

DESCRIPTION = f"""
### AI Endpoints

This router, included under the `/ai` prefix, handles endpoints related to AI models used to score and analyse token data.

It likely provides APIs for AI-related tasks such as machine learning classification of source code, natural language processing and other AI-driven applications on {TITLE}.

### Liquidity Endpoints

This router, included under the `/liquidity` prefix, handles endpoints related to token liquidity such as holder information, clustering holders and producing a liquidity report.

It provides APIs for querying the holder distribution of a token, clustering holders based on their token holdings, or other liquidity-related functionalities.

### Token Endpoints

This router, included under the `/token` prefix, handles general endpoints related to the token itself.

It provides APIs for querying the token name and symbol, the total supply, or other token-related functionalities. It also provides APIs for querying social media links and other metadata, alongside modifying the token metadata in storage.

### Search Endpoints

This router, included under the `/search` prefix, handles endpoints related to search functionalities.

It likely provides APIs for searching and retrieving data from platform storage, such as search by keywords, filtering options, or advanced search criteria.

At present, it supports only a POST request for searching by query string.

### Source Code Endpoints

This router, included under the `/sourcecode` prefix, handles endpoints related to source code operations.

It provides APIs for source code retrieval, source code caching and storage, or other source code-related functionalities derived from external API providers.
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
