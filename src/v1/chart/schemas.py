from pydantic import BaseModel, root_validator
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
    totalVolume: float = None
    data: List[ChartData]

    @root_validator(pre=True)
    def pre_process(cls, values):
        totalVolume = 0
        for data in values['data']:
            if isinstance(data, dict):
                totalVolume += data['volume'] * data['price']
            elif isinstance(data, ChartData):
                totalVolume += data.volume * data.price
        values['totalVolume'] = totalVolume
        return values
