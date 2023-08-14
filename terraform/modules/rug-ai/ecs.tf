resource "aws_ecr_repository" "rug_ai" {
  name = "${var.stage}-${var.workspace}-rug-ai"
}


resource "aws_secretsmanager_secret" "RUG_API_ETHERSCAN_API_KEY" {
  name = "RUG_API_ETHERSCAN_API_KEY"
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

module "rug_app_service" {
  source                      = "git::https://github.com/diffusion-io/rug-terraform.git//modules/ecs-with-loadbalancer?ref=v0.0.5"
  
  prefix                      = "rug-ai"
  region                      = var.region
  stage                       = var.stage
  workspace                   = var.workspace
  account_id                  = var.account_id
  secret_manager_arns = [
    aws_secretsmanager_secret.RUG_API_ETHERSCAN_API_KEY.arn,
  ]
  ssm_arns                    = ["arn:aws:ssm:${var.region}:${var.account_id}:parameter/*"] //TODO each portal-frontend should start with reserved word
  lb_arn                      = aws_alb.rug_ai.arn
  cluster_id                  = data.aws_ssm_parameter.ecs_cluster_id_parameter_store.value
  cluster_name                = data.aws_ssm_parameter.ecs_cluster_name_parameter_store.value
  container_port              = 80
  autoscaling_enabled         = var.autoscaling_enabled
  autoscaling_cpu_target      = 70
  autoscaling_max_capacity    = 4
  backend_config = {
    cpu    = 256
    memory = 512
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
  tf_environment                          = [
    {
      name  = "version"
      value = "v0.0.7"
    },
    {
      name = "ETHEREUM_BLOCK_EXPLORER_URL"
      value = "https://api.etherscan.io/api"
    },
    {
      name =  "ML_API_URL"
      value = data.aws_ssm_parameter.rug_ml_api_endpoint_parameter_store.value
    }
  ]
  alb_certifcate_arn                      = aws_acm_certificate.cert.arn
  secrets                                 = [
    {
      name      = "ETHEREUM_BLOCK_EXPLORER_API_KEY"
      valueFrom = aws_secretsmanager_secret.RUG_API_ETHERSCAN_API_KEY.arn
    }
  ]
  custom_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["dynamodb:*"]
        Effect   = "Allow"

        Resource = [
          "*"
        ]
      }
    ]
  }

}

