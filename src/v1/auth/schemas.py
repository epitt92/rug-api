from pydantic import BaseModel
from typing import List

class ChartData(BaseModel):
    timestamp: int
    price: float
    volume: float
    marketCap: float
