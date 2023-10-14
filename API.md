# API Endpoints

## Table of Contents

- [API Endpoints](#api-endpoints)
  - [Table of Contents](#table-of-contents)
  - [Authentication with AWS Cognito](#authentication-with-aws-cognito)
  - [Response Formatting](#response-formatting)
    - [Authentication Errors](#authentication-errors)
  - [Rate Limiting](#rate-limiting)
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

## Endpoint Documentation

### Authentication Endpoints

-- Not Yet Implemented --

### Token Endpoints

-- Not Yet Implemented --

### Feed Endpoints

-- Not Yet Implemented --

### Chart Endpoints

-- Not Yet Implemented --
