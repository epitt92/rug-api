from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.etherscan import *

app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://example.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Import and include the item router
from core.schemas.goplus import goplusrouter
from core.schemas.schema import etherscanrouter
app.include_router(item_router, prefix="/items", tags=["items"])
