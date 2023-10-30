import time, os, logging, math, json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List
from dotenv import load_dotenv
from decimal import Decimal
from botocore.exceptions import ClientError
from pydantic import ValidationError

from src.v1.shared.dependencies import get_primary_key, get_chain, get_rpc_provider
from src.v1.shared.schemas import ScoreResponse, Score
from src.v1.shared.DAO import DAO, DatabaseQueueObject
from src.v1.shared.models import ChainEnum, validate_token_address
from src.v1.shared.cloud_task_creator import create_http_task_rug_cf
from src.v1.shared.exceptions import (
    RugAPIException,
    DatabaseLoadFailureException,
    DatabaseInsertFailureException,
    GoPlusDataException,
    UnsupportedChainException,
    OutputValidationError,
    BlockExplorerDataException,
)

from src.v1.tokens.constants import (
    HOLDERS_STALENESS_THRESHOLD,
    SUPPLY_REPORT_STALENESS_THRESHOLD,
    TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD,
    TOKEN_METRICS_STALENESS_THRESHOLD,
    CLUSTERING_REPORT_STALENESS_THRESHOLD,
)
from src.v1.tokens.dependencies import get_supply_summary, get_transferrability_summary
from src.v1.tokens.dependencies import (
    get_go_plus_summary,
    get_block_explorer_data,
    get_go_plus_data,
    call_fetch_token_holders,
    call_total_supply,
)
from src.v1.tokens.schemas import (
    Holder,
    Cluster,
    ClusterResponse,
    AIComment,
    AISummary,
    TokenMetadata,
    ContractResponse,
    AISummary,
    SimulationResponse,
)

from src.v1.auth.endpoints import decode_token

load_dotenv()

router = APIRouter()

######################################################
#                                                    #
#                Database Adapters                   #
#                                                    #
######################################################

SUPPLY_REPORT_DAO = DAO(table_name="supplyreports")
TRANSFERRABILITY_REPORT_DAO = DAO(table_name="transferrabilityreports")
TOKEN_METRICS_DAO = DAO(table_name="tokenmetrics")
CLUSTER_REPORT_DAO = DAO(table_name="clusterreports")
HOLDERS_DAO = DAO(table_name="holders")
TOKEN_ANALYSIS_DAO = DAO(table_name="tokenanalysis")


CLUSTERING_QUEUE = DatabaseQueueObject(
    table_name="clusterreports",
    queue_url=os.environ.get("CLUSTERING_QUEUE"),
    staleness=CLUSTERING_REPORT_STALENESS_THRESHOLD,
)

######################################################
#                                                    #
#                     Endpoints                      #
#                                                    #
######################################################


@router.get(
    "/simulations/{chain}/{token_address}",
    response_model=SimulationResponse,
    dependencies=[Depends(decode_token)],
    include_in_schema=True,
)
async def get_simulation_info(
    chain: ChainEnum, token_address: str = Depends(validate_token_address)
):
    supply_summary, transferrability_summary = await get_supply_transferrability_info(
        chain, token_address
    )
    return SimulationResponse(
        supplySummary=supply_summary, transferrabilitySummary=transferrability_summary
    )


async def get_supply_transferrability_info(
    chain: ChainEnum, token_address: str = Depends(validate_token_address)
):
    _token_address = token_address.lower()

    pk = get_primary_key(_token_address, chain)

    # Load existing data for the requested token if it exists
    try:
        _supply_summary = SUPPLY_REPORT_DAO.find_most_recent_by_pk(pk)
    except ClientError as e:
        logging.error(
            f"Exception: Boto3 exception whilst fetching data from 'supplyreports' with PK: {pk}"
        )
        raise DatabaseLoadFailureException()
    except Exception as e:
        logging.error(
            f"Exception: Unknown exception whilst fetching data from 'supplyreports' with PK: {pk}"
        )
        logging.error(f"Exception: {e}")
        raise DatabaseLoadFailureException()

    try:
        _transferrability_summary = TRANSFERRABILITY_REPORT_DAO.find_most_recent_by_pk(
            pk
        )
    except ClientError as e:
        logging.error(
            f"Exception: Boto3 exception whilst fetching data from 'transferrabilityreports' with PK: {pk}"
        )
        raise DatabaseLoadFailureException()
    except Exception as e:
        logging.error(
            f"Exception: Unknown exception whilst fetching data from 'transferrabilityreports' with PK: {pk}"
        )
        logging.error(f"Exception: {e}")
        raise DatabaseLoadFailureException()

    found = False

    # If this data is found and is not stale, return it
    if _supply_summary and _transferrability_summary:
        # Check whether values are stale based on UNIX timestamp comparisons
        supply_summary_is_not_stale = (
            time.time() - int(_supply_summary.get("timestamp"))
        ) < SUPPLY_REPORT_STALENESS_THRESHOLD
        transferrability_summary_is_not_stale = (
            time.time() - int(_transferrability_summary.get("timestamp"))
        ) < TRANSFERRABILITY_REPORT_STALENESS_THRESHOLD

        if supply_summary_is_not_stale and transferrability_summary_is_not_stale:
            logging.warning(
                f"A non-stale report was found, checking whether all data is present."
            )

            supply_summary = _supply_summary.get("summary")
            transferrability_summary = _transferrability_summary.get("summary")

            if supply_summary and transferrability_summary:
                logging.warning(
                    f"Requested data is present in the database, setting `found = True` and continuing."
                )
                found = True
            else:
                logging.warning(
                    f"A non-stale report was found but one of the summary values was null. Re-calculating and re-caching..."
                )
        else:
            logging.warning(
                f"A previous report was found but it did not pass the staleness check."
            )

    if not found:
        logging.debug(
            f"Previous non-stale report was not found, fetching data from GoPlus API..."
        )

        try:
            data = get_go_plus_data(chain, _token_address)
        except Exception as e:
            logging.error(f"Exception: Raised in call to `get_go_plus_data`: {e}")
            raise GoPlusDataException(chain, _token_address)

        # Process this data and produce a supply and a transferrability summary
        try:
            supply_summary = get_supply_summary(data)
        except Exception as e:
            logging.error(
                f"Exception: An exception occurred whilst processing the supply summary for {token_address} on chain {chain}."
            )
            raise GoPlusDataException(chain, _token_address)

        try:
            transferrability_summary = get_transferrability_summary(data)
        except Exception as e:
            logging.error(
                f"Exception: An exception occurred whilst processing the transferrability summary for {token_address} on chain {chain}."
            )
            raise GoPlusDataException(chain, _token_address)

        # Cache this data to the `supplyreports` table
        try:
            SUPPLY_REPORT_DAO.insert_new(
                partition_key_value=pk,
                item={"timestamp": int(time.time()), "summary": dict(supply_summary)},
            )
        except ClientError as e:
            logging.error(
                f"Exception: Whilst writing to 'supplyreports' using `insert_new` for PK: {pk}"
            )
            raise DatabaseInsertFailureException()
        except Exception as e:
            logging.error(
                f"Exception: Whilst writing to 'supplyreports' using `insert_new` for PK: {pk}"
            )
            raise DatabaseInsertFailureException()

        # Cache this data to the `transferrabilityreports` table
        try:
            TRANSFERRABILITY_REPORT_DAO.insert_new(
                partition_key_value=pk,
                item={
                    "timestamp": int(time.time()),
                    "summary": dict(transferrability_summary),
                },
            )
        except ClientError as e:
            logging.error(
                f"Exception: Whilst writing to 'transferrabilityreports' using `insert_new` for PK: {pk}"
            )
            raise DatabaseInsertFailureException()
        except Exception as e:
            logging.error(
                f"Exception: Whilst writing to 'transferrabilityreports' using `insert_new` for PK: {pk}"
            )
            raise DatabaseInsertFailureException()

    # Format the data and return it
    try:
        supply_summary = ContractResponse(
            items=supply_summary.get("items"),
            score=supply_summary.get("score"),
            description=None,
            summaryDescription=supply_summary.get("summary"),
        )
    except ValidationError as e:
        logging.error(
            f"Exception: A ValidationError was raised for `supply_summary`: {e.json()}"
        )
        raise OutputValidationError()
    except Exception as e:
        logging.error(
            f"Exception: An uncaught exception occurred was raised for `supply_summary`: {e}"
        )
        raise OutputValidationError()

    try:
        transferrability_summary = ContractResponse(
            items=transferrability_summary.get("items"),
            score=transferrability_summary.get("score"),
            description=None,
            summaryDescription=transferrability_summary.get("summary"),
        )
    except ValidationError as e:
        logging.error(
            f"Exception: A ValidationError was raised for `transferrability_summary`: {e.json()}"
        )
        raise OutputValidationError()
    except Exception as e:
        logging.error(
            f"Exception: An uncaught exception occurred was raised for `transferrability_summary`: {e}"
        )
        raise OutputValidationError()

    logging.info(
        f"Supply and transferrability summary for {token_address} on chain {chain} fetched successfully."
    )
    return supply_summary, transferrability_summary


@router.get(
    "/metadata/{chain}/{token_address}",
    dependencies=[Depends(decode_token)],
    include_in_schema=True,
)
async def get_token_metrics(
    chain: ChainEnum, token_address: str = Depends(validate_token_address)
):
    pk = get_primary_key(token_address, chain)

    # Attempt to fetch the latest token metrics row from the database
    try:
        _token_metrics = TOKEN_METRICS_DAO.find_most_recent_by_pk(pk)
    except ClientError as e:
        logging.error(
            f"Exception: Boto3 exception whilst fetching data from 'tokenmetrics' with PK: {pk}"
        )
        raise DatabaseLoadFailureException()
    except Exception as e:
        logging.error(
            f"Exception: Unknown exception whilst fetching data from 'tokenmetrics' with PK: {pk}"
        )
        logging.error(f"Exception: {e}")
        raise DatabaseLoadFailureException()

    found = False

    if _token_metrics:
        token_metrics_last_updated = _token_metrics.get("timestamp")
        token_metrics_is_not_stale = (
            time.time() - int(token_metrics_last_updated)
        ) < TOKEN_METRICS_STALENESS_THRESHOLD

        if token_metrics_is_not_stale:
            logging.debug(
                f"Token metrics for {token_address} on chain {chain} are not stale. Setting `found = True`."
            )
            found = True
        else:
            logging.debug(
                f"A previous token metrics report was found but it did not pass the staleness check:"
            )
            logging.debug(
                f"Token metrics staleness: {time.time() - int(token_metrics_last_updated)}"
            )
            logging.debug(f"Re-calculating token metrics and re-caching...")

    if not found:
        logging.debug(
            f"Attempting to fetch all metrics data from external endpoints..."
        )

        # Fetch the data from all sources and then cache it in the database
        lastUpdatedTimestamp = int(time.time())

        # First, check whether the address corresponds to a smart contract
        # If not, throw a HTTP 404 exception
        try:
            rpc = get_rpc_provider(chain)
            checksum_address = rpc.to_checksum_address(token_address)
            is_token = rpc.eth.get_code(checksum_address).decode(
                "utf-8", errors="replace"
            )

            if len(is_token) == 0:
                raise HTTPException(
                    status_code=404,
                    detail=f"Token address {token_address} on chain {chain} is not a token.",
                )
        except Exception as e:
            logging.error(e)

            raise HTTPException(
                status_code=404,
                detail=f"Token address {token_address} on chain {chain} is not a token.",
            )

        # Fetch and process market data from GoPlus
        try:
            market_data = get_go_plus_summary(chain, token_address)
        except Exception as e:
            logging.warning(
                f"Exception: Failed to fetch GoPlus data for {token_address} on chain {chain}. Using empty dictionary and continuing..."
            )
            market_data = {}

        # Fetch and process token social data from Etherscan
        try:
            explorer_data = get_block_explorer_data(chain, token_address)
        except Exception as e:
            logging.warning(
                f"Failed to fetch block explorer data for {token_address} on chain {chain}. Using empty dictionary and continuing..."
            )
            explorer_data = {}

        # TODO: This check cannot occur because CoinGecko has heavy rate-limiting
        # TODO: The backend service cannot call CoinGecko directly, this will be fixed when we create a backend service for this

        # try:
        #     # Fetch latestPrice information from chart data
        #     chart = await get_chart_data(chain, _token_address, FrequencyEnum.one_day)
        #     if chart:
        #         market_data['latestPrice'] = chart.latestPrice if isinstance(chart, ChartResponse) else chart.get('latestPrice')
        # except Exception as e:
        #     logging.warning(f'Failed to fetch chart data as part of `info` for {_token_address} on chain {chain}. Using empty dictionary and continuing...')
        #     market_data['latestPrice'] = None

        _token_metrics = {
            "timestamp": lastUpdatedTimestamp,
            "summary": {
                **market_data,
                **explorer_data,
                **{"lastUpdatedTimestamp": lastUpdatedTimestamp},
            },
        }

        # Change floating point fields in the token metrics to Decimal type
        for key in _token_metrics["summary"]:
            if isinstance(_token_metrics["summary"][key], float):
                _token_metrics["summary"][key] = Decimal(
                    str(_token_metrics["summary"][key])
                )

        try:
            TOKEN_METRICS_DAO.insert_new(partition_key_value=pk, item=_token_metrics)
        except ClientError as e:
            logging.error(
                f"Failed to cache token metrics for {token_address} on chain {chain}."
            )
            raise DatabaseInsertFailureException()
        except Exception as e:
            logging.error(
                f"An unknown exception occurred which was not caught by boto3 exception handling..."
            )
            raise DatabaseInsertFailureException()

    _token_metrics = {
        **_token_metrics["summary"],
        **{"tokenAddress": token_address, "chain": get_chain(chain)},
    }

    try:
        output = TokenMetadata(**_token_metrics)
    except ValidationError as e:
        logging.error(
            f"Exception: A ValidationError was raised for `output`: {e.json()}"
        )
        raise OutputValidationError()
    except Exception as e:
        logging.error(
            f"Exception: An uncaught exception occurred was raised for `output`: {e}"
        )
        raise OutputValidationError()

    return output


@router.get(
    "/audit/{chain}/{token_address}",
    dependencies=[Depends(decode_token)],
    include_in_schema=True,
)
async def get_token_audit_summary(
    chain: ChainEnum, token_address: str = Depends(validate_token_address)
):
    _chain = chain.value if isinstance(chain, ChainEnum) else str(chain)

    # If the chain is unsupported, raise the correct exception to handle this
    if _chain != "ethereum":
        raise UnsupportedChainException(chain=_chain)

    # PK for lookup in DB and message for, if there is no data in the DB, make the queue request
    pk = get_primary_key(token_address=token_address, chain=chain)

    # Try to fetch the data from the database
    db_response = TOKEN_ANALYSIS_DAO.find_most_recent_by_pk(partition_key_value=pk)

    if db_response is None:
        # TODO: Switch this on during production
        # create_http_task_rug_cf(
        #     json_payload={"token_address": token_address, "chain": chain.value}
        # )

        return JSONResponse(
            status_code=202,
            content={
                "status_code": 202,
                "detail": f"Token {token_address} on chain {chain.value} was queued for audit analysis.",
            },
        )

    description = db_response.get("summaryText")

    overallScore = float(db_response.get("tokenScore"))
    files = db_response.get("files")
    numIssues = sum([len(item.get("result")) for item in files])

    logging.debug(
        f"Audit report for {token_address} on chain {chain.value} fetched successfully. Score: {overallScore}, numIssues: {numIssues}."
    )

    comments = []
    for smart_contract in files:
        for issue in smart_contract.get("result"):
            lines = issue.get("lines")

            if lines:
                lines = [int(item) for item in lines]

            try:
                comment = AIComment(
                    commentType="Function",
                    title=issue.get("title"),
                    description=issue.get("description"),
                    severity=issue.get("level"),
                    fileName=smart_contract.get("fileName"),
                    sourceCode=[issue.get("function_code")],
                    lines=lines,
                )

                comments.append(comment)
            except ValidationError as e:
                logging.error(
                    f"Exception: A ValidationError was raised while adding an issue to the list of comments: {e} {issue}"
                )
                continue
            except Exception as e:
                logging.error(
                    f"Exception: An unknown Exception was raised while adding an issue to the list of comments: {e} {issue}"
                )
                continue

    try:
        output = AISummary(
            description=description,
            numIssues=numIssues,
            overallScore=overallScore,
            comments=comments,
        )
        return output
    except ValidationError as e:
        logging.error(
            f"Exception: A ValidationError was raised while formatting the AISummary response object: {e}"
        )
        raise OutputValidationError()
    except Exception as e:
        logging.error(
            f"Exception: An unknown Exception was raised while formatting the AISummary response object: {e}"
        )
        raise OutputValidationError()


@router.get(
    "/cluster/{chain}/{token_address}",
    dependencies=[Depends(decode_token)],
    include_in_schema=True,
)
async def get_token_clustering(
    chain: ChainEnum, token_address: str = Depends(validate_token_address)
):
    _chain = chain.value if isinstance(chain, ChainEnum) else str(chain)

    # If the chain is unsupported, raise the correct exception to handle this
    if _chain != "ethereum":
        raise UnsupportedChainException(chain=_chain)

    # Get the pk for DB lookup, and the message data for the queue (if there is no data in the DB)
    pk = get_primary_key(token_address, chain)
    message_data = {"token_address": token_address, "chain": chain.value}

    # TODO: There is repeated logic inside lambda that allows to fetch_holders, get_cluster_response
    # TODO: We have duplicated code also in the src.v1.clustering, maybe create a package
    response = CLUSTERING_QUEUE.get_item(
        pk=pk, MessageGroupId=f"cluster_{pk}", message_data=message_data
    )

    if response is None:
        return JSONResponse(
            status_code=202,
            content={
                "status_code": 202,
                "detail": f"Token {token_address} on chain {_chain} was queued for cluster analysis.",
            },
        )

    if response.get("data"):
        return {
            **json.loads(response.get("data")),
            "timestamp": response.get("timestamp"),
        }
    else:
        logging.error(
            f"Exception: Token {token_address} on chain {_chain} was returned but had no data."
        )
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "detail": f"Token {token_address} on chain {_chain} was returned but had no data.",
            },
        )


@router.get(
    "/holderchart/{chain}/{token_address}",
    dependencies=[Depends(decode_token)],
    include_in_schema=True,
)
async def get_holder_chart(
    chain: ChainEnum,
    token_address: str = Depends(validate_token_address),
    numClusters: int = 5,
):
    _chain = chain.value if isinstance(chain, ChainEnum) else str(chain)

    # If the chain is unsupported, raise the correct exception to handle this
    if _chain != "ethereum":
        raise UnsupportedChainException(chain=chain)

    cluster_summary = await get_token_clustering(chain, token_address)

    if not cluster_summary or isinstance(cluster_summary, JSONResponse):
        logging.info(
            f"Exception: No cluster summary was found for {token_address} on chain {chain}."
        )
        try:
            data = fetch_holders(token_address=token_address, chain=chain)
        except Exception as e:
            logging.error(
                f"Exception: Whilst trying to obtain `holders` for {token_address} on chain {chain}: {e}"
            )
            raise RugAPIException()

        try:
            top_holders = sorted(
                data.keys(), key=lambda k: data[k]["percentTokens"], reverse=True
            )[:numClusters]
            holders = {holder: data[holder] for holder in top_holders}

            clusters = [
                Cluster(
                    members=[
                        Holder(
                            address=holder,
                            numTokens=float(holders[holder]["numTokens"]),
                            percentage=float(holders[holder]["percentTokens"]),
                        )
                    ]
                )
                for holder in holders
            ]
            return ClusterResponse(clusters=clusters)
        except ValidationError as e:
            logging.error(
                f"Exception: A ValidationError occurred whilst formatting the clustering response for {token_address} on chain {chain}: {e}"
            )
            raise OutputValidationError()
        except Exception as e:
            logging.error(
                f"Exception: An unknown Exception occurred whilst formatting the clustering response for {token_address} on chain {chain}: {e}"
            )
            raise OutputValidationError()

    # Fetch components
    components = cluster_summary.get("components")[:numClusters]

    clusters = []
    for component in components:
        nodes, nodePercentages = (
            component.get("nodes"),
            component.get("nodePercentages"),
        )
        label = component.get("componentType")

        if len(nodes) != len(nodePercentages):
            logging.error(
                f"Exception: Length of nodes was {len(nodes)} and length of percentages array was {len(nodePercentages)}."
            )
            raise Exception()

        try:
            members = [
                Holder(address=nodes[i], percentage=nodePercentages[i])
                for i in range(len(nodes))
            ]
            clusters.append(Cluster(members=members, label=label))
        except ValidationError as e:
            logging.error(
                f"Exception: A ValidationError occurred whilst formatting the components response for {token_address} on chain {chain}: {e}"
            )
            raise OutputValidationError()
        except Exception as e:
            logging.error(
                f"Exception: An unknown Exception occurred whilst formatting the components response for {token_address} on chain {chain}: {e}"
            )
            raise OutputValidationError()

    try:
        output = ClusterResponse(clusters=clusters)
        return output
    except ValidationError as e:
        logging.error(
            f"Exception: A ValidationError occurred whilst formatting the ClusterResponse for {token_address} on chain {chain}: {e}"
        )
        raise OutputValidationError()
    except Exception as e:
        logging.error(
            f"Exception: An unknown Exception occurred whilst formatting the ClusterResponse for {token_address} on chain {chain}: {e}"
        )
        raise OutputValidationError()


def fetch_holders(token_address: str, chain: ChainEnum):
    _token_address = token_address.lower()
    pk = get_primary_key(chain.value, _token_address)

    # Attempt to fetch holders from DAO object
    logging.info(
        f"Attempting to find holders for token {token_address} on chain {chain.value} in the database..."
    )
    holders = HOLDERS_DAO.find_most_recent_by_pk(pk)

    # If holders are found, check if they are stale
    if holders:
        logging.info(
            f"Holders found for token {token_address} on chain {chain.value} in the database."
        )
        timestamp = int(holders.get("timestamp"))
        if time.time() - timestamp < HOLDERS_STALENESS_THRESHOLD:
            logging.info(
                f"Holders for token {token_address} on chain {chain.value} are not stale, returning..."
            )
            return holders.get("holders")

    logging.info(
        f"Holders for token {token_address} on chain {chain.value} are stale or not found in the database, fetching from the blockchain..."
    )
    data = call_fetch_token_holders(chain=chain.value, token_address=token_address)
    total_supply = call_total_supply(token_address=token_address)

    if data.get("status") and data["status"] == "1":
        result = data.get("result")
        output = {}
        for item in result:
            address, numTokens = (
                item.get("TokenHolderAddress"),
                int(item.get("TokenHolderQuantity")),
            )
            output[address] = {
                "numTokens": numTokens,
                "percentTokens": Decimal(str(numTokens / total_supply)),
            }

        # Reduce the size of the holders object to top holders
        if len(output) > 1000:
            top_holders = sorted(
                output.keys(), key=lambda k: output[k]["percentTokens"], reverse=True
            )[:1000]
            output = {holder: output[holder] for holder in top_holders}

        # Save transfers to DAO object
        logging.error(
            f"Saving holders to DAO object for token {token_address} on chain {chain.value}"
        )

        try:
            HOLDERS_DAO.insert_new(
                partition_key_value=pk,
                item={"timestamp": int(time.time()), "holders": output},
            )
        except ClientError as e:
            logging.error(
                f"Error saving holders to DAO object for token {token_address} on chain {chain.value}: {e}"
            )
            logging.error(f"Primary key used for database insertion: {pk}")
            raise e

    return output


@router.get(
    "/score/{chain}/{token_address}",
    response_model=ScoreResponse,
    dependencies=[Depends(decode_token)],
    include_in_schema=True,
)
async def get_score_info(
    chain: ChainEnum, token_address: str = Depends(validate_token_address)
):
    # Fetch required data from various sources
    try:
        supplySummary, transferrabilitySummary = await get_supply_transferrability_info(
            chain, token_address
        )

        # Format data into Score format objects
        supply = Score(
            value=supplySummary.score, description=supplySummary.summaryDescription
        )
        transferrability = Score(
            value=transferrabilitySummary.score,
            description=transferrabilitySummary.summaryDescription,
        )
    except ValidationError as e:
        logging.error(
            f"Exception: ValidationError was raised on call to format supply/transferrability into Score responses for {token_address} on chain {chain}: {e}"
        )
        supply, transferrability = Score(), Score()
    except Exception as e:
        logging.error(
            f"Exception: During call to `get_supply_transferrability_info` for {token_address} on chain {chain}."
        )
        supply, transferrability = Score(), Score()

    try:
        # Attempt to queue up the clustering job
        liquiditySummary = await get_token_clustering(chain, token_address)

        if isinstance(liquiditySummary, JSONResponse):
            if liquiditySummary.status_code == 202:
                liquidity = Score()
            else:
                logging.warning(
                    f"Exception: A JSONResponse was returned from `get_token_clustering` for {token_address} on chain {chain}."
                )
                liquidity = Score()

        try:
            liquidity = Score(
                value=liquiditySummary.get("score"),
                description=liquiditySummary.get("description"),
            )
        except Exception as e:
            logging.error(
                f"Exception: An exception occurred whilst formatting the liquidity score for {token_address} on chain {chain}."
            )
            liquidity = Score()
    except ValidationError as e:
        logging.error(
            f"Exception: ValidationError was raised on call to format into liquidity into Score responses for {token_address} on chain {chain}: {e}"
        )
        liquidity = Score()
    except Exception as e:
        logging.error(
            f"Exception: During call to `get_clustering_summary_from_cache` for {token_address} on chain {chain}."
        )
        liquidity = Score()

    try:
        # Attempt to queue up the audit job
        auditSummary = await get_token_audit_summary(chain, token_address)

        if isinstance(auditSummary, JSONResponse):
            if auditSummary.status_code == 202:
                audit = Score()
            else:
                logging.warning(
                    f"Exception: A JSONResponse was returned from `get_token_audit_summary` for {token_address} on chain {chain}."
                )
                audit = Score()

        try:
            audit = Score(value=float(auditSummary.overallScore), description=None)
        except Exception as e:
            logging.error(
                f"Exception: An exception occurred whilst formatting the audit score for {token_address} on chain {chain}: {e}"
            )
            audit = Score(value=None, description=None)
    except ValidationError as e:
        logging.error(
            f"Exception: ValidationError was raised on call to format into audit into Score responses for {token_address} on chain {chain}: {e}"
        )
        audit = Score()
    except Exception as e:
        logging.error(
            f"Exception: During call to `get_token_audit_summary` for {token_address} on chain {chain}: {e}"
        )
        audit = Score()

    scores = [supply, transferrability, liquidity, audit]

    def calculate_overall_score(scores: List[Score]) -> float:
        _scores = [score.value for score in scores]

        # Calculate and return the geometric mean of all valid score contributors

        output, N = 1.0, 0
        for score in _scores:
            if score == 0:
                return 0.0
            elif score:
                output *= score
                N += 1

        if N == 0:
            return None

        return math.pow(output, 1.0 / N)

    # Format response into ScoreResponse format object
    try:
        score = ScoreResponse(
            overallScore=calculate_overall_score(scores),
            supplyScore=supply,
            transferrabilityScore=transferrability,
            liquidityScore=liquidity,
            auditScore=audit,
        )

        return score
    except ValidationError as e:
        logging.error(
            f"Exception: A ValidationError occurred whilst formatting the ScoreResponse for {token_address} on chain {chain}: {e}"
        )
        raise OutputValidationError()
    except Exception as e:
        logging.error(
            f"Exception: An unknown Exception occurred whilst formatting the ScoreResponse for {token_address} on chain {chain}: {e}"
        )
        raise OutputValidationError()
