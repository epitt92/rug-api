# rug.ai API

`rug-api` is a microservices-based application that serves the user interface for rug.ai. Powered by Python's FastAPI, it's designed to run seamlessly on AWS.

## Table of Contents

- [rug.ai API](#rugai-api)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Architecture](#architecture)
  - [Running the Docker Container Locally](#running-the-docker-container-locally)
  - [DevOps Practices and Deployment](#devops-practices-and-deployment)
    - [Infrastructure as Code (IaC) with Terraform](#infrastructure-as-code-iac-with-terraform)
      - [Deploy Infrastructure Locally](#deploy-infrastructure-locally)
        - [Prerequisites](#prerequisites)
        - [Deployment Steps](#deployment-steps)
        - [Adding Terraform Resources to Modules](#adding-terraform-resources-to-modules)
    - [CI/CD Pipeline with Github Actions](#cicd-pipeline-with-github-actions)
    - [Trunk-Based Git Strategy](#trunk-based-git-strategy)
      - [Deploying to the Develop Environment](#deploying-to-the-develop-environment)
      - [Deploying to the Stage Environment](#deploying-to-the-stage-environment)
  - [API Endpoints](#api-endpoints)
  - [Contact](#contact)

## Features

- **FastAPI Backend**: Provides a high-performance backend API using Python's FastAPI.
- **Microservices Architecture**: Modular and scalable approach to deploy and manage services.
- **AWS Integration**: Optimized for deployment on Amazon Web Services.

## Installation

Before deploying `rug-api` on AWS, you should set it up and test your changes locally:

1. Clone the repository:
   ```sh
   git clone https://github.com/diffusion-io/rug-api.git
   ```

2. Navigate to the project directory and install required packages:
   ```sh
   cd rug-api
   pip install -r requirements.txt
   ```

3. Ensure you have created a `.env` file in the root of the repository with the required environment variables. See `.env.example` for a list of all required environment variables for this application.

4. Finally, run the application locally:
   ```sh
   uvicorn main:app --reload
   ```

## Architecture

The rug.ai API application is deployed on AWS ECS. It leverages an autoscaling group to ensure that the application scales up or down based on demand, this autoscaling functionality is managed by AWS Fargate. In front of the ECS, it also deploys a load balancer that evenly distributes incoming application traffic across multiple targets, increasing the availability of your application. The architecture follows best practices for high availability and scalability across multiple zones:

![Rug API App Architecture](https://github.com/diffusion-io/rug-api/blob/main/images/rug-api-architecture.png)

In addition, some of the application endpoints make use of other rug.ai services, such as the SQS queue service and serverless compute functions deployed as part of another rug.ai application. This API does not contain deployment details for these services, although some of the API endpoints make use of the queue service to create workloads for other deployments in the stack:

![rug api SQS ](https://github.com/diffusion-io/rug-api/blob/main/images/rug-api-SQS.png)

## Running the Docker Container Locally

1. Build the Docker image locally using `docker build`:

```bash
docker build -t rug-api .
```

2. Run the Docker container using `docker run`:

```bash
docker run -p 80:8000 rug-api
```

## DevOps Practices and Deployment

### Infrastructure as Code (IaC) with Terraform

The rug.ai API employs Terraform for an Infrastructure as Code (IaC) approach. All AWS infrastructure configurations are written as code within Terraform scripts, allowing for automated provisioning and management of resources. The Terraform state will be stored in Amazon S3 for persistent storage, while DynamoDB will be used to provide state locking, preventing simultaneous state modifications that could lead to conflicts or inconsistencies. The repository has a dedicated Terraform folder containing various modules and app infrastructure definitions.

#### Deploy Infrastructure Locally

##### Prerequisites

1. You need to have Terraform and Terragrunt installed on your local machine,
2. You need to have access to an AWS account and your AWS credentials should be configured on your local machine,
3. You need to have Git installed on your local machine, and,
4. You need to have set the Terragrunt environment variables.

##### Deployment Steps

1. First, clone the repository on your local machine:

```bash
git clone https://github.com/diffusion-io/rug-api.git
```

2. Navigate to the target module in the Terraform modules directory:

```bash 
cd rug-api/terraform/<module_name>
```

3. Initialize the module using `terragrunt`:

```bash
terragrunt init
```

4. Deploy the module using `terragrunt`:

```bash
terragrunt run-all apply
```

##### Adding Terraform Resources to Modules

1. Add the Terraform resources to the module in the Terraform modules directory,

2. Add the necessary variables to the `terragrunt.hcl` file or configuration folder, and,

3. Push to the GitHub to apply the changes by running the CI/CD pipeline or run the following command to apply the Terraform code from your local machine:

```bash
terragrunt run-all apply
```

### CI/CD Pipeline with Github Actions

Github Actions is used to implement the Continuous Integration/Continuous Deployment (CI/CD) pipeline. This automated pipeline triggers on events such as pull requests, merges, or new tags. Each workflow comprises three main jobs - testing, building, and deploying. The testing phase involves running `pytest` on the Python-based rug.ai API code to validate various endpoints and functionality. Upon successful testing, the build job executes, which compiles the code and pushes the resulting artifact to an ECR repository. Finally, the deployment job pulls this artifact and uses Terraform apply to deploy the updated infrastructure.

### Trunk-Based Git Strategy

The development workflow is based on a Trunk-Based Git strategy. This means there is one long-lived branch, the trunk, which acts as the base for all development work. Feature branches are created for new developments and are merged back into the trunk only after rigorous testing in the development environment to maintain the trunk's integrity. An optional second long-lived branch could be created for production deployments. The workflow is supplemented by a Pull-Request process, ensuring code review and quality checks before merging.

![Trunk-Based image](https://github.com/diffusion-io/rug-api/blob/main/images/trunk-based.png)

- **Pipeline (P1):** When a new feature branch is initiated and completed, create a merge request targeting the trunk branch `main`. This merge request triggers the initial pipeline. The pipeline is designed to build and deploy applications on the development environment.

- **Pipeline (P2):** Once your feature has been tested on the development environment, the merge request will be approved and merged into the `main` branch. This action triggers the second pipeline, which is responsible for building and deploying the application to the stage environment.

- **Pipeline (P3):** This pipeline will be initiated when a tag is created on the trunk `main` branch. Similar to the other pipelines, this pipeline will build and deploy only the application to the production environment.

#### Deploying to the Develop Environment

1. Create a new branch from the `main` branch:

```bash
git checkout -b <branch_name>
```

2. Make changes to the code, and commit the changes using `git`:

```bash
git add .
git commit -m "commit message"
```

3. Push the changes to the remote branch with the same branch name as you created earlier:

```bash
git push origin <branch_name>
```

4. Create a pull request from the remote branch `<branch_name>` to the `main` branch. This will trigger **Pipeline (P1)** above and will automatically build your modified code on the develop environment.

#### Deploying to the Stage Environment

Once a pull request is approved and merged to the `main` branch, a GitHub Actions run will be triggered and the application will be deployed to the stage environment account.

## API Endpoints

Documentation for the API endpoints can be accessed [here](API.md) or at `localhost:8000/endpoints` on your local deployment.

## Contact

Jake Lee - `jake@diffusion.io`
