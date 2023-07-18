from fastapi import HTTPException
from fastapi import APIRouter, HTTPException
import time
from core.models import ChartResponse, ChartData
import random, math, time

router = APIRouter()

@router.get("/{chain_id}/{token_address}", response_model=ChartResponse)
async def get_chart_data(chain_id: int, token_address: str, frequency: str = '1d'):
    if len(token_address) != 42:
        raise HTTPException(status_code=400, detail=f"Token address {token_address} is invalid.")

    N = 200
    step = 86400

    S = [random.uniform(0, 10000)]
    V = [S[0] * random.randint(200, 2000)]
    end_time = int(time.time())
    start_time = end_time - N * step

    for i in range(1, N):
        S.append(S[i-1] * math.exp(random.uniform(-0.02, 0.02)))
        V.append(S[i] * random.randint(200, 2000))

    y_min, y_max = min(S), max(S)
    l = (y_max - y_min) / 0.9
    y_min -= l * 0.05
    y_max += l * 0.05

    data = []
    for i in range(N):
        data.append(ChartData(timestamp=start_time + i * step, price=S[i], volume=V[i], marketCap=S[i] * 1e9))

    return ChartResponse(xMin=start_time, xMax=end_time, yMin=y_min, yMax=y_max, numDatapoints=N, data=data)
