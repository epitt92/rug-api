from pydantic import BaseModel
from typing import List

class ChartData(BaseModel):
    timestamp: int
    price: float
    volume: float
    marketCap: float

class ChartResponse(BaseModel):
    priceMin: float
    priceMax: float
    marketCapMin: float
    marketCapMax: float
    timestampMin: float
    timestampMax: float
    numDatapoints: int
    latestPrice: float
    latestReturn: float
    data: List[ChartData]
