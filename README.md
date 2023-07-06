# rug-api

- Ensure Python is installed on your machine, pull the repository and open it in terminal

- Call `pip install -r requirements.txt` to install package requirements

- Add a `.env` file in the root folder with `ETHERSCAN_API_KEY = 'YOUR-API-KEY'`

- Call `uvicorn server:app --reload` to run the API locally on port `8000`

- Navigate to `localhost:8000/endpoints` in browser to view the endpoints, or `localhost:8000/documentation` to view the documentation for the API

## Unit Tests

Unit tests run via `pytest tests` in the console.


## Infrastructure
The Rug API is hosted on AWS using Docker Swarm and EC2 Instances. 

![diffusion](https://github.com/diffusion-io/rug-api/assets/13097984/29335812-6ec4-44e9-8589-884c5622091d)


## Deployments
Rug API uses Github actions for deploying new changes to the AWS. The current workflow only monitor `main` branch for new changes. To deploy your branch merge it to main and it will automatically deploy to Docker Service. 

## Manually setting up the Docker Servcie
In case you need to setup the service from scratch please follow below steps:
1. Login to ECR registry
```aws ecr get-login-password --region eu-west-2 | sudo docker login --username AWS --password-stdin 379150053149.dkr.ecr.eu-west-2.amazonaws.com```

2. Create new service with 2 containers using the target image tag 
```docker service create --name rug-api -e ETHERSCAN_API_KEY=<> --replicas 2 379150053149.dkr.ecr.eu-west-2.amazonaws.com/rug-api:<tag>```


3. Update service to use new image with rolling upgrades
```docker service update --image 379150053149.dkr.ecr.eu-west-2.amazonaws.com/rug-api:<tag> --update-parallelism 1 --update-delay 10s rug-api```


## Starting Docker container locally
To start the Docker container locally 
1. Build the docker image run below from project repo:
``` sudo docker build -t rug-api:latest . ```

2. Start container from above image
``` sudo docker run -ti -e ETHERSCAN_API_KEY=<> -p 80:80 rug-api:latest ```

