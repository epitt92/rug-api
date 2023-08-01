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
    latestMarketCap: float
    latestReturn: float
    totalVolume: float = None
    dayVolume: float = None
    elapsedNumDays: float = None
    avgCandleDurationMins: float = None
    data: List[ChartData]

    @root_validator(pre=True)
    def pre_process(cls, values):
        totalVolume = 0
        dayVolume = 0
        for data in values['data']:
            if isinstance(data, dict):
                totalVolume += data['volume']
                if data['timestamp'] > values['timestampMax'] - 86400:
                    dayVolume += data['volume']
            elif isinstance(data, ChartData):
                totalVolume += data.volume
                if data.timestamp > values['timestampMax'] - 86400:
                    dayVolume += data.volume
        values['totalVolume'] = totalVolume
        values['dayVolume'] = dayVolume
        values['elapsedNumDays'] = (values['timestampMax'] - values['timestampMin']) / 86400
        values['avgCandleDurationMins'] = (values['timestampMax'] - values['timestampMin']) / (60 * values['numDatapoints'])
        return values
