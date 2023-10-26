from fastapi import HTTPException

from src.v1.chart.schemas import ChartResponse, ChartData


def process_market_data(market_data):
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

    # CoinGecko returns data in reverse chronological order
    for i in reversed(range(N)):
        row = market_data[i]
        timestamp, price, volume, marketCap = row[0], row[4], row[5], row[4]

        timestampArray.append(timestamp)
        priceArray.append(price)
        marketCapArray.append(marketCap)

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
