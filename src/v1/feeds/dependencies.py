import time, boto3, logging, json, requests, random
from botocore.exceptions import BotoCoreError, ClientError
from decimal import Decimal
from datetime import datetime, timedelta

from src.v1.shared.constants import CHAIN_ID_MAPPING, CHAIN_SYMBOL_MAPPING
from src.v1.shared.dependencies import get_rpc_provider
from src.v1.feeds.exceptions import TimestreamWriteException
from src.v1.feeds.constants import *
from src.v1.feeds.schemas import MarketDataResponse


def process_row(row):
    if row["Data"][6].get("ScalarValue") is None:
        value = row["Data"][7]["ScalarValue"]
    else:
        value = row["Data"][6]["ScalarValue"]

    return {
        "eventHash": row["Data"][0]["ScalarValue"],
        "address": row["Data"][1]["ScalarValue"],
        "blockchain": row["Data"][2]["ScalarValue"],
        "timestamp": row["Data"][3]["ScalarValue"],
        "measureName": row["Data"][4]["ScalarValue"],
        "time": row["Data"][5]["ScalarValue"],
        "value": value,
    }


def convert_floats_to_decimals(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_floats_to_decimals(value)
        return data
    elif isinstance(data, list):
        return [convert_floats_to_decimals(item) for item in data]
    elif isinstance(data, float):
        return Decimal(str(data))
    else:
        return data


def get_swap_link(dex, network, token_address):
    SWAP_URLS = {
        "uniswapv2": f"https://app.uniswap.org/swap?chain={network}&inputCurrency={token_address}",
        "uniswapv3": f"https://app.uniswap.org/swap?chain={network}&inputCurrency={token_address}",
        "pancakeswapv2": f"https://pancakeswap.finance/swap?chain={CHAIN_SYMBOL_MAPPING[network]}&inputCurrency={token_address}",
        "pancakeswapv3": f"https://pancakeswap.finance/swap?chain={CHAIN_SYMBOL_MAPPING[network]}&inputCurrency={token_address}",
        "sushiswap": f"https://app.sushi.com/swap?chainId={CHAIN_ID_MAPPING[network]}&inputCurrency={token_address}",
        "baseswap": f"https://baseswap.fi/swap?inputCurrency={token_address}",
        "rocketswap": f"https://rocketswap.exchange/swap?chain={network}&inputCurrency={token_address}",
        "traderjoe": f"https://traderjoexyz.com/{network}/trade?inputCurrency={token_address}",
    }

    if dex not in SWAP_URLS:
        logging.error(f"Exception: Unsupported DEX {dex}")
        raise ValueError(f"Unsupported DEX: {dex}")

    return SWAP_URLS[dex]


class TimestreamEventAdapter:
    def __init__(self, database: str = "rug_api_db") -> None:
        self.database = database
        self.interval = 1

        self.client = boto3.client("timestream-write", region_name="eu-west-1")

    @staticmethod
    def get_type(value):
        if isinstance(value, str):
            return "VARCHAR"
        elif isinstance(value, float) or isinstance(value, int):
            return "DOUBLE"
        elif isinstance(value, bool):
            return "BOOLEAN"
        else:
            try:
                _ = str(value)
                return "VARCHAR"
            except:
                raise Exception(f"Measure value {value} could not be typed.")

    def generate_record_measures(self, key, value):
        return {
            "MeasureName": key,
            "MeasureValue": str(value),
            "MeasureValueType": self.get_type(value),
        }

    @staticmethod
    def generate_dimensions(table_name: str, data: str):
        if table_name == "eventlogs":
            return {
                "Dimensions": [
                    {"Name": "event_hash", "Value": data.get("event_hash")},
                ]
            }
        elif table_name == "reviewlogs":
            return {
                "Dimensions": [
                    {"Name": "token_address", "Value": data.get("token_address")},
                    {"Name": "chain", "Value": data.get("chain")},
                ]
            }
        else:
            raise Exception(f"Table name {table_name} not recognised.")

    def generate_record(self, dimensions, key, value):
        record = {
            **dimensions,
            **{"Time": str(int(time.time())), "TimeUnit": "SECONDS"},
            **self.generate_record_measures(key, value),
        }

        return record

    def generate_records(self, table_name: str, data: dict):
        dimensions = self.generate_dimensions(table_name, data)

        records = []
        records.append(self.generate_record(dimensions, "user_id", data.get("user_id")))
        return records

    def post(self, table_name: str, message: dict):
        try:
            records = self.generate_records(table_name, message)
        except Exception as e:
            message = f"Exception: An error occurred whilst generating records: {e}"
            logging.error(message)
            raise TimestreamWriteException(message=message)

        logging.info(f"Records: {records}")
        try:
            response = self.client.write_records(
                DatabaseName=self.database, TableName=table_name, Records=records
            )
            _ = response["ResponseMetadata"]["HTTPStatusCode"]
        except ClientError as e:
            # Handle specific Boto3 client errors
            if e.response["Error"]["Code"] == "ThrottlingException":
                message = f"Exception: Error code {e.response['Error']['Code']}. Request was throttled. Consider retrying the request with exponential backoff."
                logging.error(message)
                raise TimestreamWriteException(message=message)
            elif e.response["Error"]["Code"] == "ValidationException":
                message = f"Exception: Error code {e.response['Error']['Code']}. A Validation Error: {e}"
                logging.error(message)
                raise TimestreamWriteException(message=message)
            elif e.response["Error"]["Code"] == "ResourceNotFoundException":
                message = f"Exception: Error code {e.response['Error']['Code']}. The database or table does not exist."
                logging.error(message)
                raise TimestreamWriteException(message=message)
            elif e.response["Error"]["Code"] == "RejectedRecordsException":
                message = f"Exception: Error code {e.response['Error']['Code']}. Rejected records: {e}"
                rejected_records = e.response["Error"]["RejectedRecords"]
                for record in rejected_records:
                    logging.error(
                        f"Record {record['RecordIndex']} was rejected due to: {record['Reason']}"
                    )
                raise TimestreamWriteException(message=message)
            else:
                # Rethrow the error if it is not one that we expected
                message = f"Exception: Error code {e.response['Error']['Code']}. An unexpected error: {e}"
                logging.error(message)
                raise TimestreamWriteException(message=message)
        except BotoCoreError as e:
            # Handle errors inherent to the core boto3 (like network issues)
            message = f"Exception: BotoCore Error: {e}"
            logging.error(message)
            raise TimestreamWriteException(message=message)
        except Exception as e:
            message = f"Exception: An unknown error occurred: {e}"
            logging.error(message)
            raise TimestreamWriteException(message=message)



decoder = lambda x: ftfy.fix_text(x.decode("utf-8", errors="ignore")).strip()
int_decoder = lambda b: int.from_bytes(b, "big")


def get_usd_price(symbol):
    url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol}&tsyms=USD"
    request_response = requests.get(url)
    request_response.raise_for_status()

    data = request_response.json()
    price = data.get("USD")
    if price:
        return Decimal(price)
    else:
        return 0


def get_pools(chain, token_address):
    print("-------------------------------")
    lower_address = token_address.lower()
    chain_id = CHAIN_ID_MAPPING[chain]
    # Get the leading pool address from GoPlus API for a token and return it
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={lower_address}"

    request_response = requests.get(url)
    request_response.raise_for_status()

    data = request_response.json()
    pair_addresses = data.get("result").get(lower_address).get("dex")

    return pair_addresses


def get_block_from_24h_ago(w3):
    current_block = w3.eth.getBlock("latest")
    target_timestamp = datetime.now().timestamp() - timedelta(days=1).total_seconds()

    while current_block["timestamp"] > target_timestamp:
        # Decrease block number to go back in time
        current_block = w3.eth.getBlock(current_block["number"] - 1)

    return current_block["number"]


def get_metadata(token_address, network):
    start_time = time.time()
    w3 = get_rpc_provider(network)

    token_address_ = w3.to_checksum_address(token_address)

    # process_multicall = Multicall(w3, network)

    # Define your token's contract address and create a contract object
    # token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

    metadata_analytics_contract = w3.eth.contract(
        address=METADATA_ANALYTICS_ADDRESS[network], abi=METADATA_ANALYTICS_ABI
    )

    pools = POOL_INDEXER[network].get(token_address.lower())
    if pools == None or len(pools) == 0:
        return None

    total_market_caps = 0
    total_liquidity = 0
    pool_count = 0

    # Multicall
    # calls = []

    # for pool_data in pools:
    #     pool_address = pool_data["pair"]

    #     if pool_data["name"] == "UniswapV3":
    #         calls.append(process_multicall.create_call(metadata_analytics_contract, 'getUniswapV3Data', args=[pool_address, token_address]))
    #     else:
    #         calls.append(process_multicall.create_call(metadata_analytics_contract, 'getUniswapV2Data', args=[pool_address, token_address]))

    # results = process_multicall.call(calls)

    # for idx, pool_data in enumerate(pools):
    #     # Extracting results
    #     if results[idx][0] == False:
    #         continue
    #     liquidity_raw = int_decoder(results[idx][1])
    #     market_cap_raw = int_decoder(results[idx][2])
    #     stable_token_addr = decoder(results[idx][3])
    #     stable_token_decimals = int_decoder(results[idx][4])

    #     symbol = SYMBOLS[network][stable_token_addr.lower()]
    #     stable_token_price = get_usd_price(symbol)

    #     # Adjust for stableTokenDecimals and multiply by token price in USD
    #     liquidity_usd = (liquidity_raw * stable_token_price / (10 ** stable_token_decimals))
    #     market_cap_usd = (market_cap_raw * stable_token_price / (10 ** stable_token_decimals))

    #     total_market_caps += market_cap_usd
    #     total_liquidity += liquidity_usd
    #     pool_count += 1

    # Single call
    for pool_data in pools:
        pool_address = pool_data["address"]

        pool_address_ = w3.to_checksum_address(pool_address)
        if pool_data["dex"] == "UniswapV3":
            result = metadata_analytics_contract.functions.getUniswapV3Data(
                pool_address_, token_address_
            ).call()
        else:
            result = metadata_analytics_contract.functions.getUniswapV2Data(
                pool_address_, token_address_
            ).call()

        # Extracting results
        liquidity_raw, market_cap_raw, stable_token_addr, stable_token_decimals = result

        symbol = SYMBOLS[network].get(stable_token_addr.lower())

        if symbol is None:
            # TODO: @ilce Add handling for this case
            continue

        stable_token_price = get_usd_price(symbol)

        # Adjust for stableTokenDecimals and multiply by token price in USD
        liquidity_usd = liquidity_raw * stable_token_price / (10**stable_token_decimals)
        market_cap_usd = (
            market_cap_raw * stable_token_price / (10**stable_token_decimals)
        )

        total_market_caps += market_cap_usd
        total_liquidity += liquidity_usd
        pool_count += 1

        # start_time = time.time()
        # # start_block = get_block_from_24h_ago(w3)
        # start_block = w3.eth.getBlock("latest")["number"] - 7200
        # print(f"It took {(time.time() - start_time):.3f} to get the block number 24h ago.")

        # start_time = time.time()
        # events_filter = pool_contract.events.Swap.createFilter(
        #     fromBlock=start_block, toBlock="latest"
        # )
        # events = events_filter.get_all_entries()
        # if pool_data["name"] == "UniswapV3":
        #     volume_24h = sum([event["args"]["amount0"] for event in events])
        # else:
        #     volume_24h = sum(
        #         [
        #             event["args"]["amount0In"] + event["args"]["amount0Out"]
        #             for event in events
        #         ]
        #     )

        # volume_24h = volume_24h * token_price_usd * 2
        # print(
        #     f"It took {(time.time() - start_time):.3f} to get all events and calculate the volume."
        # )

    # Calculate the average market cap and total liquidity across all pools
    average_market_cap = total_market_caps / pool_count if pool_count else 0
    print(f"Market capacity: {average_market_cap}")
    print(f"Liquidity: {total_liquidity}")
    # print(f"24H Volume: {volume_24h}")
    print(f"Market Capacity and Liquidity took {(time.time() - start_time):.3f}.")
    print("-------------------------------")
    return MarketDataResponse(marketCap=average_market_cap, liquidityUsd=total_liquidity)
