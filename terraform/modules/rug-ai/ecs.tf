resource "aws_ecr_repository" "rug_ai" {
  name = "${var.stage}-${var.workspace}-rug-ai"
}


data "aws_ssm_parameter" "ecs_cluster_id_parameter_store" {
  name = "/rug/ecs/cluster/id"
}

data "aws_ssm_parameter" "ecs_cluster_name_parameter_store" {
  name = "/rug/ecs/cluster/name"
}


data "aws_ssm_parameter" "rug_ml_api_endpoint_parameter_store" {
  name = "/rug/ml/api/endpoint"
}

data "aws_ssm_parameter" "rug_ml_audit_queue_arn_parameter_store" {
  name = "/rug/ml/audit/queue/arn"
}

data "aws_ssm_parameter" "rug_ml_cluster_queue_arn_parameter_store" {
  name = "/rug/ml/cluster/queue/arn"
}

data "aws_ssm_parameter" "rug_timestream_db_arn_parameter_store" {
  provider = aws.eu-west-1
  name     = "/rug_feed/timestream_db_arn"
}

module "rug_app_service" {
  source = "git::https://github.com/diffusion-io/rug-terraform.git//modules/ecs-with-loadbalancer?ref=v0.0.9"

  prefix                   = "rug-ai"
  region                   = var.region
  stage                    = var.stage
  workspace                = var.workspace
  account_id               = var.account_id
  ssm_arns                 = ["arn:aws:ssm:${var.region}:${var.account_id}:parameter/*"] //TODO each portal-frontend should start with reserved word
  lb_arn                   = aws_alb.rug_ai.arn
  cluster_id               = data.aws_ssm_parameter.ecs_cluster_id_parameter_store.value
  cluster_name             = data.aws_ssm_parameter.ecs_cluster_name_parameter_store.value
  desired_count            = 2
  container_port           = 80
  autoscaling_enabled      = var.autoscaling_enabled
  autoscaling_cpu_target   = 70
  autoscaling_max_capacity = 8
  autoscaling_min_capacity = 2
  backend_config = {
    cpu    = var.stage == "dev" ? 512 : 1024
    memory = var.stage == "dev" ? 1024 : 2048
  }
  docker_image_backend                    = replace("${var.rug_ecr_image}", " ", "")
  gitlab_credentials_parameter_secret_arn = ""
  aws_ecs_task_definition_stopTimeout     = 2
  deregistration_delay                    = 5
  target_group_healthy_threshold          = 2
  unhealthy_threshold                     = 2
  target_group_interval                   = 6
  health_check_port                       = 80
  health_check_matcher                    = "200-499"
  health_check_path                       = "/"
  aws_security_group_loadbalancer_id      = aws_security_group.rug_ai.id
  tf_environment = [
    {
      name  = "version"
      value = "v0.0.8"
    },
    {
      name  = "ETHEREUM_BLOCK_EXPLORER_URL"
      value = "https://api.etherscan.io/api"
    },
    {
      name  = "ARBITRUM_BLOCK_EXPLORER_URL"
      value = "https://api.arbiscan.io/api"
    },
    {
      name  = "BASE_BLOCK_EXPLORER_URL"
      value = "https://api.basescan.org/api"
    },
    {
      name  = "BNB_BLOCK_EXPLORER_URL"
      value = "https://api.bscscan.com/api"
    },
    {
      name  = "ML_API_URL"
      value = data.aws_ssm_parameter.rug_ml_api_endpoint_parameter_store.value
    },
    {
      name = "COGNITO_USER_POOL_ID"
      value = aws_cognito_user_pool.user_pool.id
    },
    {
      name = "COGNITO_APP_CLIENT_ID"
      value = aws_cognito_user_pool_client.client.id
    },
    {
      name = "CLUSTERING_QUEUE"
      value = data.aws_ssm_parameter.rug_ml_cluster_queue_arn_parameter_store.value
    },
    {
      name = "TOKEN_ANALYSIS_QUEUE"
      value = data.aws_ssm_parameter.rug_ml_audit_queue_arn_parameter_store.value
    }
  ]
  alb_certifcate_arn = aws_acm_certificate.cert.arn
  secret_manager_arns = [
    aws_secretsmanager_secret.ETHEREUM_BLOCK_EXPLORER_API_KEY.arn,
    aws_secretsmanager_secret.ARBITRUM_BLOCK_EXPLORER_API_KEY.arn,
    aws_secretsmanager_secret.BASE_BLOCK_EXPLORER_API_KEY.arn,
    aws_secretsmanager_secret.BNB_BLOCK_EXPLORER_API_KEY.arn,
    aws_secretsmanager_secret.RUG_API_ETHEREUM_RPC_URL.arn,
    aws_secretsmanager_secret.RUG_API_ARBITRUM_RPC_URL.arn,
    aws_secretsmanager_secret.RUG_API_BASE_RPC_URL.arn,
    aws_secretsmanager_secret.GO_PLUS_APP_KEY.arn,
    aws_secretsmanager_secret.GO_PLUS_APP_SECRET.arn
  ]
  secrets = [
    {
      name      = "ETHEREUM_BLOCK_EXPLORER_API_KEY"
      valueFrom = aws_secretsmanager_secret.ETHEREUM_BLOCK_EXPLORER_API_KEY.arn
    },
    {
      name      = "ARBITRUM_BLOCK_EXPLORER_API_KEY"
      valueFrom = aws_secretsmanager_secret.ARBITRUM_BLOCK_EXPLORER_API_KEY.arn
    },
    {
      name      = "BASE_BLOCK_EXPLORER_API_KEY"
      valueFrom = aws_secretsmanager_secret.BASE_BLOCK_EXPLORER_API_KEY.arn
    },
    {
      name      = "BNB_BLOCK_EXPLORER_API_KEY"
      valueFrom = aws_secretsmanager_secret.BNB_BLOCK_EXPLORER_API_KEY.arn
    },
    {
      name     = "ETHEREUM_RPC_URL"
      valueFrom = aws_secretsmanager_secret.RUG_API_ETHEREUM_RPC_URL.arn
    },
    {
      name     = "ARBITRUM_RPC_URL"
      valueFrom = aws_secretsmanager_secret.RUG_API_ARBITRUM_RPC_URL.arn
    },
    {
      name     = "BASE_RPC_URL"
      valueFrom = aws_secretsmanager_secret.RUG_API_BASE_RPC_URL.arn
    },
    {
      name     = "GO_PLUS_APP_KEY"
      valueFrom = aws_secretsmanager_secret.GO_PLUS_APP_KEY.arn
    },
    {
      name     = "GO_PLUS_APP_SECRET"
      valueFrom = aws_secretsmanager_secret.GO_PLUS_APP_SECRET.arn
    }
  ]
  custom_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Action = ["dynamodb:*"]
        Effect = "Allow"

        Resource = [
          "*"
        ]
      },
      {
        Action = ["timestream:*"]
        Effect = "Allow"
        Resource = [
          # data.aws_ssm_parameter.rug_timestream_db_arn_parameter_store.value
          "*"
        ]
      },
      {
        //cognito actions
        Action = ["cognito-idp:AdminDeleteUser", "cognito-idp:AdminConfirmSignUp", "cognito-idp:AdminCreateUser", "cognito-idp:ConfirmSignUp", "cognito-idp:ResendConfirmationCode", "cognito-idp:ForgotPassword", "cognito-idp:ConfirmForgotPassword", "cognito-idp:SignUp", "cognito-idp:InitiateAuth"]
        Effect = "Allow"
        Resource = [
          aws_cognito_user_pool.user_pool.arn
        ]
      }
    ]
  }

}
