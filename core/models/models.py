from pydantic import BaseModel
from typing import List

class RugAPIResponse(BaseModel):
    status: int
    message: str
    result: dict

class RugAPISearchResponse(BaseModel):
    status: int
    message: str
    result: List[dict]

class RugAPIStringResponse(BaseModel):
    status: int
    message: str
    result: str

def response(result):
    return RugAPIResponse(status=1, message="OK", result=result)

def search(result):
    return RugAPISearchResponse(status=1, message="OK", result=result)

def success(result):
    return RugAPIStringResponse(status=1, message="OK", result=result)

def error(reason: str):
    return RugAPIStringResponse(status=0, message="NOTOK", result=reason)
