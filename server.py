from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse

from router import v1_router

TITLE = 'rug.ai API'
VERSION = 1.12

def custom_schema():
    openapi_schema = get_openapi(title=TITLE, version=VERSION, routes=app.routes)
    openapi_schema["info"] = {"title": TITLE, "version": VERSION}
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app = FastAPI(docs_url="/endpoints", redoc_url="/documentation", title=TITLE, favicon='https://rug.ai/favicon.ico')
app.openapi = custom_schema
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "rug-api"}

app.include_router(v1_router)
