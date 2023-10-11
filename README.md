# rug-api

`rug-api` is a microservices-based application that serves the user interface for rug.ai. Powered by Python's FastAPI, it's designed to run seamlessly on AWS.

## Table of Contents

- [rug-api](#rug-api)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Deployment on AWS](#deployment-on-aws)
  - [Usage](#usage)
  - [API Endpoints](#api-endpoints)
  - [Contact](#contact)

## Features

- **FastAPI Backend**: Provides a high-performance backend API using Python's FastAPI.
- **Microservices Architecture**: Modular and scalable approach to deploy and manage services.
- **AWS Integration**: Optimized for deployment on Amazon Web Services.

## Installation

Before deploying `rug-api` on AWS, you need to set it up locally:

1. Clone the repository:
   ```sh
   git clone https://github.com/diffusion-io/rug-api.git
   ```

2. Navigate to the project directory and install required packages:
   ```sh
   cd rug-api
   pip install -r requirements.txt
   ```

3. Run the application locally:
   ```sh
   uvicorn main:app --reload
   ```

## Deployment on AWS

TODO @rawanb9:
- Add deployment architecture diagram
- Add deployment details

## Usage

Once the application is running, navigate to the provided IP and port in your browser to access the rug.ai user interface.

## API Endpoints

Documentation for the API endpoints can be accessed at `localhost:8000/endpoints` on your local deployment.

## Contact

Jake Lee - `jake@diffusion.io`
