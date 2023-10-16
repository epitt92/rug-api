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
    - [Database Access Object (DAO)](#database-access-object-dao)
      - [DAO Functions:](#dao-functions)
    - [Redis Access Object (RAO)](#redis-access-object-rao)
      - [RAO Functions:](#rao-functions)
    - [Database Queue Access Object (DQAO)](#database-queue-access-object-dqao)
      - [DQAO Functions:](#dqao-functions)
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
2. Redis Access Object Interraction:
   1. If the data is present in Redis and is fresh, the system directly responds to the API request.
   2. If the data is stale or not present, the flow moves to check DynamoDB.
3. Database Access Object Interaction:
   1. The system checks for data presence in DynamoDB.
   2. If fresh data is found, it responds directly to the request.
   3. If the data is stale, it queues a job to calculate the data and responds with the stale data.
   4. If no data is found, it checks if there's an SQS queue available.
4. Queue Interaction:
   1. If there's an SQS queue, the request message is sent to the SQS to initiate the data calculation process.
   2. Upon completion, the fresh data is calculated with the connection open, then cached in DynamoDB and stored in Redis for faster future accesses.
5. Data Calculation and Response:
   1. If there's no SQS queue, the system calculates the data with the connection open.
   2. Once the data is calculated, it is responded to the request and also cached in both DynamoDB and Redis.

### Database Access Object (DAO)
Role: Responsible for interacting directly with Amazon DynamoDB.
Key Operations:
Get data from DynamoDB.
Cache data in DynamoDB with a typical expiry of 30 minutes.
Template for DAO:

#### DAO Functions:

- **Function Name**: [Function Name]
    - **Description**: [Brief Description]
    - **Parameters**:
        1. [Parameter Name]: [Description]
    - **Return Type**: [Return Type]
  
### Redis Access Object (RAO)
Role: Manages interactions with Amazon ElasticCache/Redis.
Key Operations:
Retrieve key from Redis.
Cache data in Redis.
Template for RAO:

#### RAO Functions:

- **Function Name**: [Function Name]
    - **Description**: [Brief Description]
    - **Parameters**:
        1. [Parameter Name]: [Description]
    - **Return Type**: [Return Type]

### Database Queue Access Object (DQAO)
Role: Handles queue interactions and data fetch operations.
Key Operations:
Get data/key from the queue.
Template for DQAO:

#### DQAO Functions:

- **Function Name**: [Function Name]
    - **Description**: [Brief Description]
    - **Parameters**:
        1. [Parameter Name]: [Description]
    - **Return Type**: [Return Type]

## Endpoint Documentation

### Authentication Endpoints

-- Not Yet Implemented --

### Token Endpoints

-- Not Yet Implemented --

### Feed Endpoints

-- Not Yet Implemented --

### Chart Endpoints

-- Not Yet Implemented --
