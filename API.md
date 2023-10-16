# API Endpoints

## Table of Contents

- [API Endpoints](#api-endpoints)
  - [Table of Contents](#table-of-contents)
  - [Authentication with AWS Cognito](#authentication-with-aws-cognito)
  - [Response Formatting](#response-formatting)
    - [Authentication Errors](#authentication-errors)
  - [Rate Limiting](#rate-limiting)
  - [Data Architecture](#data-architecture)
    - [Step-by-Step Flow](#step-by-step-flow)
    - [Redis Access Object (RAO)](#redis-access-object-rao)
      - [Overview](#overview)
      - [Attributes](#attributes)
      - [Methods](#methods)
        - [`generate_key(pk: str) -> str`](#generate_keypk-str---str)
        - [`put(pk: str, data: dict)`](#putpk-str-data-dict)
        - [`get(pk: str) -> dict`](#getpk-str---dict)
    - [Database Access Object (DAO)](#database-access-object-dao)
      - [Overview](#overview-1)
      - [Attributes](#attributes-1)
      - [Methods](#methods-1)
        - [`find_all_by_pk(partition_key_value: str) -> List[Dict[Any, Any]]`](#find_all_by_pkpartition_key_value-str---listdictany-any)
        - [`find_most_recent_by_pk(partition_key_value: str) -> Dict[Any, Any]`](#find_most_recent_by_pkpartition_key_value-str---dictany-any)
        - [`find_count_by_pk(partition_key_value: str) -> int`](#find_count_by_pkpartition_key_value-str---int)
        - [`insert_one(partition_key_value: str, item: Dict[Any, Any]) -> None`](#insert_onepartition_key_value-str-item-dictany-any---none)
        - [`insert_new(partition_key_value: str, item: Dict[Any, Any]) -> None`](#insert_newpartition_key_value-str-item-dictany-any---none)
    - [Database Queue Object (DQO)](#database-queue-object-dqo)
      - [Overview](#overview-2)
      - [Arguments](#arguments)
      - [Attributes](#attributes-2)
      - [Methods](#methods-2)
        - [`get_item(pk: str, MessageGroupId: str, message_data: dict) -> Optional[dict]`](#get_itempk-str-messagegroupid-str-message_data-dict---optionaldict)
  - [Endpoint Documentation](#endpoint-documentation)
    - [Authentication Endpoints](#authentication-endpoints)
    - [Token Endpoints](#token-endpoints)
    - [Feed Endpoints](#feed-endpoints)
    - [Chart Endpoints](#chart-endpoints)

## Authentication with AWS Cognito

The API employs JWT authentication using AWS Cognito in combination with the `fastapi_jwt_auth` library. AWS Cognito handles user registration, authentication, and other account-related operations. Upon successful authentication, AWS Cognito issues JWT tokens to authorized users. The API, in turn, utilizes `fastapi_jwt_auth` to validate these JWT tokens, using the Cognito pool's JWT URL for token verification. This ensures that only valid, authenticated requests access the API's protected resources.

For the API to process requests to protected endpoints, it's imperative to provide a valid JWT token as part of the request headers. Clients must include this token within the `Authorization` header of their requests. The expected format is `Bearer <YOUR_JWT_TOKEN>`. Without this token, or if an invalid or expired token is provided, the API will return an authentication error, preventing access to the requested resources.

## Response Formatting

All endpoints implement JSON response formatting, with HTTP status codes. Unsuccessful requests will additionally return a response body with the following format:

```
{
    "detail": "An unexpected and uncaught exception was raised during an API call."
}
```

The `"detail"` key is used to indicate what happened during the API execution, and in addition is used by specific endpoints to indicate what should be rendered on the user interface. For instance, queries which require downstream compute jobs will return responses as follows:

```
{
   "status_code": 202, # Status Code
   "detail": f"Token {token_address} on chain {_chain} was queued for cluster analysis." # Response Body
}
```

where the `"status_code"` indicates that the job is queued, and should be used to inform front-end rendering.

### Authentication Errors

In addition, any endpoint which requires authentication and for which the supplied access token was invalid will return a response with HTTP status code `403`. This should be used to navigate the user away from sensitive data and back to the log-in screen.

## Rate Limiting

-- Not Yet Implemented --

## Data Architecture

In an attempt to reduce the amount of concurrently open connections and increase the responsiveness of the service, the service employs database and in-memory caching to attempt to serve requests more efficiently and reduce the end-to-end latency of the system. The following architecture diagram demonstrates the logical flow of data manipulation and fetching upon receiving an API request, detailing the interactions between deployed services including Amazon ElasticCache (Redis), Amazon DynamoDB, and other integrated components such as the queue system:

![rug API Data Flow ](https://github.com/diffusion-io/rug-api/blob/main/images/rug-api-data.png)

### Step-by-Step Flow

1. API Request Initiation:
   1. The process begins with a user-initiated API request.
   2. The system first checks whether the required data is present in Redis.
2. **Redis Access Object** Interraction:
   1. If the data is present in Redis and is fresh, the system directly responds to the API request.
   2. If the data is stale or not present, the flow moves to check DynamoDB.
3. **Database Access Object** Interaction:
   1. The system checks for data presence in DynamoDB.
   2. If fresh data is found, it responds directly to the request.
   3. If the data is stale, it queues a job to calculate the data but responds immediately with the stale data.
   4. If no data is found, it checks if there's an SQS queue available.
4. Queue Interaction:
   1. If there's an SQS queue available for this request, the request parameters are sent to SQS queue to initiate the data calculation process.
   2. The user is served an immediate response with HTTP status code 202, indicating that the request is queued.
   3. Upon completion, the fresh data is then cached in DynamoDB and stored in Redis for faster future accesses.
5. Data Calculation and Response:
   1. If there's no SQS queue for this request, the system calculates the data with the connection open.
   2. Once the data is calculated, it is sent to the user in response to the request and also cached in both DynamoDB and Redis.

### Redis Access Object (RAO)
The `RAO` class provides a mechanism to store and retrieve data from an AWS ElastiCache Redis instance, essentially acting as a caching layer for DAO object queries.

#### Overview

To instantiate the `RAO`, the user must provide a `prefix` key which will be used to prefix all data stored in the cache. For `RAO` objects instantiated as part of a Database Access Object, this `prefix` will correspond to the table in the corresponding database for which the `RAO` acts as a caching layer:

```RAO(prefix: str)```

**Arguments:**

- `prefix`: The unique prefix for all data stored in the cache.

#### Attributes

- `client_url`: The URL of the Redis server (specified by an environment variable for the Redis instance).
- `client_port`: The port on which the Redis server is running (specified by an environment variable for the Redis instance).
- `prefix`: The unique prefix for all data stored in the cache.
- `tte`: Time-To-Expiry for cached keys (default is 30 minutes or 1800 seconds).
- `client`: An instance of the `redis.Redis` object that connects to the Redis server.

#### Methods

##### `generate_key(pk: str) -> str`

Generates a unique key for storage in Redis based on the table name and the primary key (pk).

**Arguments:**

- `pk`: Primary key (usually a unique identifier) for the data you want to cache.

**Returns:**

A unique string key to be used for data storage in Redis. This key is the concatenation given by the f-string `f"{prefix}_{pk}`.

##### `put(pk: str, data: dict)`
Stores data associated with the given primary key (pk) in the Redis cache.

**Arguments:**

- `pk`: Primary key (usually a unique identifier) for the data you want to cache.
- `data`: The data (in dictionary format) you want to cache.

**Note:**

- The data is stored in a JSON-serialized string format.
- The cached data will expire after the specified tte (Time-To-Expiry) duration.

##### `get(pk: str) -> dict`
Retrieves data from the Redis cache based on the given primary key (`pk`).

**Arguments:**

- `pk`: Primary key (usually a unique identifier) for the data you want to retrieve.

**Returns:**

The cached data (in dictionary format) associated with the provided primary key.
Returns `None` if the key is not found in the cache.

**Note:**

- This class assumes that there is a `REDIS_URL` and a `REDIS_PORT` as environment variables which specify the URL and port for the Redis server. If these are not provided, it defaults to creating a Redis client with default settings (assuming a localhost deployment of Redis).
- This object has `redis` and `json` modules as dependencies, and these should be imported prior to instantiating the `RAO`.

### Database Access Object (DAO)
The DAO class facilitates the storage and retrieval of data from an AWS DynamoDB table. It provides a set of methods for interacting with a specified DynamoDB table, abstracting away the complexities associated with the direct use of the boto3 library for DynamoDB.

#### Overview

To initialize the DAO, users need to provide a table_name, which corresponds to the DynamoDB table they intend to interact with. Additionally, they can specify a region_name to target a specific AWS region:

```DAO(table_name: str, region_name: str = 'eu-west-2')```

**Arguments:**

- `table_name`: Name of the DynamoDB table.
- `region_name`: AWS region where the table resides (default is `'eu-west-2'`).

#### Attributes

- `table_name`: Name of the specified DynamoDB table.
- `table`: DynamoDB table object from `boto3`.
- `partition_key_name`: Name of the table's partition key.
- `partition_range_name`: Name of the table's range key (if present).

#### Methods

##### `find_all_by_pk(partition_key_value: str) -> List[Dict[Any, Any]]`

Retrieve all records that match a specific partition key value.

**Arguments:**

- `partition_key_value`: Value of the partition key to search for.

**Returns:**

A list of dictionaries, each representing a record that matches the provided partition key value.

##### `find_most_recent_by_pk(partition_key_value: str) -> Dict[Any, Any]`

Fetch the most recent record corresponding to a specific partition key value.

**Arguments:**

- `partition_key_value`: Value of the partition key to search for.

**Returns:**

A dictionary representing the most recent record that matches the given partition key value, or `None` if no match is found.

##### `find_count_by_pk(partition_key_value: str) -> int`

Count the number of records that match a specific partition key value.

**Arguments:**

- `partition_key_value`: Value of the partition key to count.

**Returns:**

An integer representing the number of records that match the given partition key value.

##### `insert_one(partition_key_value: str, item: Dict[Any, Any]) -> None`

Insert a record into the DynamoDB table with a specific partition key value.

**Arguments:**

- `partition_key_value`: Value for the partition key of the item to be inserted.
- `item`: Dictionary containing the item data.

**Raises:**

- `ConditionalCheckFailedException`: This exception is raised if a record with the same partition key value already exists in the table.

##### `insert_new(partition_key_value: str, item: Dict[Any, Any]) -> None`

Insert a record with a specific partition key value. Unlike insert_one, this method does not check for the existence of a record with the same partition key value.

**Arguments:**

- `partition_key_value`: Value for the partition key of the item to be inserted.
- `item`: Dictionary containing the item data.

**Notes:**

- This class requires the `boto3` library to interface with AWS DynamoDB.
- Ensure proper AWS configurations and credentials are set, either as environment variables or in the AWS credentials file.
- Before using the `DAO` class, users must ensure the specified DynamoDB table exists and has a partition key defined.
- The class automatically determines the names of the partition key and (if present) range key of the specified table upon instantiation.
  
### Database Queue Object (DQO)

The `DQO` class facilitates interactions with both AWS DynamoDB and Amazon Simple Queue Service (SQS). It combines the data access capabilities of DynamoDB with the queuing mechanisms of SQS, allowing for asynchronous processing and updating of data.

#### Overview

To initialize the `DQO`, users provide a table_name (for DynamoDB), a queue_url (for SQS), an optional region_name to target a specific AWS region, and an optional staleness parameter:

```DatabaseQueueObject(table_name: str, queue_url: str, region_name: str = 'eu-west-2', staleness: Optional[int] = None)```

#### Arguments

- `table_name`: Name of the DynamoDB table.
- `queue_url`: URL for the desired SQS queue.
- `region_name`: AWS region (default is `'eu-west-2')`.
- `staleness`: Duration (in seconds) to determine if an item is considered stale (optional).

#### Attributes

- `DAO`: An instance of the previously defined `DAO` class for DynamoDB interactions.
- `sqs`: Client object for interacting with Amazon SQS.
- `queue_url`: URL of the desired SQS queue.
- `staleness`: Duration (in seconds) used to determine item staleness.

#### Methods

##### `get_item(pk: str, MessageGroupId: str, message_data: dict) -> Optional[dict]`

Retrieve the most recent item from DynamoDB using a partition key. If the item does not exist or is considered stale, a new message is sent to SQS to trigger an update or creation process.

**Arguments:**

- `pk`: Partition key to search in DynamoDB.
- `MessageGroupId`: Message group ID for sending the message to SQS.
- `message_data`: Dictionary containing data to send as a message to SQS.

**Returns:**

An `Optional[dict]`: If the item is found in DynamoDB and is not stale, the method returns the item. If the item does not exist or is stale, a message is created in SQS, and the method returns `None`.

**Logic:**

- If the requested item is not found in DynamoDB or is considered stale (based on the staleness attribute), a message is sent to SQS.
- This message prompts an external process (e.g., an AWS Lambda function) to create or update the corresponding item in DynamoDB.
- The Lambda function or equivalent service processes the message from SQS, updates/creates the DynamoDB record, and then removes the message from SQS.
- Any additional messages in the SQS queue with the same `MessageGroupId` will be ignored by the Lambda function, but it will still be triggered, which may lead to inefficiencies.

**Notes:**

- This class requires the `boto3` library to interface with both AWS DynamoDB and Amazon SQS.
- Proper AWS configurations and credentials should be set, either as environment variables or in the AWS credentials file.
- Ensure that both the specified DynamoDB table and SQS queue exist prior to using the `DAO`.

## Endpoint Documentation

### Authentication Endpoints

-- Not Yet Implemented --

### Token Endpoints

-- Not Yet Implemented --

### Feed Endpoints

-- Not Yet Implemented --

### Chart Endpoints

-- Not Yet Implemented --
