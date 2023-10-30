from fastapi import HTTPException
import time, numpy as np

from src.v1.chart.schemas import ChartResponse, ChartData


def process_market_data(market_data, duration):
    # Refactor response to correct formatting
    N = len(market_data)

    if N == 0:
        raise Exception(
            f"Failed to fetch any market data. The length of the array returned was 0."
        )

    output = []
    timestampArray = []
    priceArray = []
    marketCapArray = []
    volumeArray = []

    current_time = int(time.time())
    cutoff_time = current_time - duration

    # CoinGecko returns data in reverse chronological order
    for i in reversed(range(N)):
        row = market_data[i]
        timestamp, price, volume, marketCap = row[0], row[4], row[5], row[4]

        # Only include data points that are within the cutoff time
        if timestamp > cutoff_time:
            timestampArray.append(timestamp)
            priceArray.append(price)
            marketCapArray.append(marketCap)
            volumeArray.append(volume)

    # Sort arrays by timestamp
    indexes = np.argsort(timestampArray)

    for index in indexes:
        timestamp = timestampArray[index]
        price = priceArray[index]
        volume = volumeArray[index]
        marketCap = marketCapArray[index]

        output.append(
            ChartData(
                timestamp=timestamp, price=price, volume=volume, marketCap=marketCap
            )
        )

    timestampMin = min(timestampArray)
    timestampMax = max(timestampArray)
    priceMin = min(priceArray)
    priceMax = max(priceArray)

    # Modify priceMin and priceMax to add buffers
    l = (priceMax - priceMin) / 0.9
    priceMin -= l * 0.05
    priceMax += l * 0.05

    return ChartResponse(
        priceMin=priceMin,
        priceMax=priceMax,
        marketCapMin=priceMin,
        marketCapMax=priceMax,
        timestampMin=timestampMin,
        timestampMax=timestampMax,
        numDatapoints=N,
        data=output,
        latestPrice=priceArray[-1],
        latestMarketCap=marketCapArray[-1],
        latestReturn=(priceArray[-1] - priceArray[0]) / priceArray[0],
    )
