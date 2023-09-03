from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse

import dotenv

from router import v1_router

dotenv.load_dotenv()

TITLE = 'rug.ai API'
VERSION = "2.0"


app = FastAPI(docs_url="/endpoints", redoc_url="/documentation", title=TITLE, version=VERSION, favicon='https://rug.ai/favicon.ico')
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "rug-api"}

app.include_router(v1_router)
