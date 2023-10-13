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

## Architecture

The Rug API application is deployed on AWS ECS. We leverage an autoscaling group to ensure that the application scales up or down based on demand. In front of the ECS, we have a load balancer that evenly distributes incoming application traffic across multiple targets, increasing the availability of your application.

The architecture follows best practices for high availability and scalability.

![Rug API App Architecture](https://github.com/diffusion-io/rug-api/blob/main/images/rug-api-architecture.png)

![rug api SQS ](https://github.com/diffusion-io/rug-api/blob/main/images/rug-api-SQS.png)

## Run the docker container locally

1. Build the docker image

```bash
docker build -t rug-api .
```

2. Run the docker container

```bash
docker run -p 80:8000 rug-api
```

## Devops practices

### Infrastructure as Code (IaC) with Terraform

The RUG solution will employ Terraform for its Infrastructure as Code (IaC) approach. All AWS infrastructure configurations are written as code within Terraform scripts, allowing for automated provisioning and management of resources. The Terraform state will be stored in Amazon S3 for persistent storage, while DynamoDB will be used to provide state locking, preventing simultaneous state modifications that could lead to conflicts or inconsistencies. The repository has a dedicated Terraform folder containing various modules and app infrastructure definitions.

#### Deploy Infrastructures from local machine  

##### Pre-requisites:

1. You need to have Terraform and Terragrunt installed on your local machine.
2. You need to have access to an AWS account and your AWS credentials should be configured on your local machine.
3. You need to have Git installed on your local machine.
4. set the Terragrunt environment variables

##### Steps:

1. Clone the repository:

```bash
git clone https://github.com/diffusion-io/rug-api.git
```

2. Navigate to the target module in terraform directory

```bash 
cd rug-api/terraform/<module_name>
```

3. Initialize the module

```bash
terragrunt init
```

4. Deploy the module

```bash
terragrunt run-all apply
```
##### add terraform resources to the module

1. add the terraform resources to the module in the terraform directory

2. add the necessary variables to the terragrunt.hcl file or config folder

3. push to the github to apply the changes by the pipeline or run the following command to apply the terraform code

```bash
terragrunt run-all apply
```

### CI/CD Pipelines with Github Actions

Github Actions is used to implement the Continuous Integration/Continuous Deployment (CI/CD) pipeline. This automated pipeline triggers on events such as pull requests, merges, or new tags. Each workflow comprises three main jobs - testing, building, and deploying. The testing phase involves running pytest on the Python-based RUG code to validate various functions. Upon successful testing, the build job executes, which compiles the code and pushes the resulting artifact to an ECR repository. Finally, the deployment job pulls this artifact and uses terraform apply to deploy the updated infrastructure.

### Trunk-Based Git Strategy

The development workflow is based on the Trunk-Based Git strategy. This means there is one long-lived branch, the trunk, which acts as the base for all development work. Feature branches are created for new developments and are merged back into the trunk only after rigorous testing in the development environment to maintain the trunk's integrity. An optional second long-lived branch could be created for production deployments. The workflow is supplemented by a Pull-Request process, ensuring code review and quality checks before merging.

![Trunk-Based image](https://github.com/diffusion-io/rug-api/blob/main/images/trunk-based.png)

Pipeline (P1): When a new feature branch is initiated and completed, create a merge request targeting the trunk branch - "main". This merge request triggers the initial pipeline. The pipeline is designed to build and deploy applications.

Pipeline (P2): Once your feature has been tested on the dev env, the merge request will be approved and merged into the main branch. This action triggers the second pipeline, which is responsible for building and deploying the application to the stage environment.

Pipeline (P3): This pipeline will be initiated when a tag is created on the trunk branch. Similar to the other pipelines, this pipeline will build and deploy only the application to the production environment.

### deploy to dev env

1. Create a new branch from the main branch

```bash
git checkout -b <branch_name>
```

2. Make changes to the code

3. Commit the changes

```bash
git add .
git commit -m "commit message"
```

4. Push the changes to the remote branch

```bash
git push origin <branch_name>
```

5. Create a pull request from the branch to the main branch

this will deploy the app to the dev environment account

### deploy to stage env

1. once the pull request is approved and merged to the main branch, the github action will be triggered and the app will be deployed to the stage environment account



## Usage

Once the application is running, navigate to the provided IP and port in your browser to access the rug.ai user interface.

## API Endpoints

Documentation for the API endpoints can be accessed at `localhost:8000/endpoints` on your local deployment.

## Contact

Jake Lee - `jake@diffusion.io`
