from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from v1 import *

app = FastAPI()

def custom_schema():
    openapi_schema = get_openapi(
        title="Rug.ai API",
        version="1.0",
        description="RESTful API endpoints for token review metadata.",
        routes=app.routes,
    )

    openapi_schema["info"] = {
        "title": "Rug.ai API",
        "version": "1.0",
        "description": "RESTful API endpoints for token review metadata.",
    }

    app.openapi_schema = openapi_schema

    return app.openapi_schema

app.openapi = custom_schema

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(go_plus_router, prefix="/goplus", tags=["GoPlus Security Endpoints"])
app.include_router(explorer_router, prefix="/explorer", tags=["Block Explorer Endpoints"])
app.include_router(score_router, prefix="/score", tags=["Rug.ai Score Endpoints"])
app.include_router(honeypot_router, prefix="/honeypot", tags=["Honeypot.is Endpoints"])
