
include {
  path = find_in_parent_folders("terragrunt.hcl")
}

locals {
  source      = get_env("TG_ENV", "dev")
  workspace   = get_env("TG_WORKSPACE", "default")
  env_config  = read_terragrunt_config(find_in_parent_folders("config/${local.source}.hcl"))
  rug_ecr_image = get_env("TG_RUG_ECR_IMAGE", "701199753814.dkr.ecr.eu-west-2.amazonaws.com/dev-default-rug-ai:f74740f8c3c97d1ed8b1561abac2afcc74c591ab")
}

terraform {
  source = "${get_parent_terragrunt_dir()}/modules/rug-ai"
}

inputs = {
  region                      = local.env_config.locals.aws_region
  account_id                  = local.env_config.locals.account_id
  stage                       = local.env_config.locals.stage
  tags                        = local.env_config.locals.tags
  workspace                   = local.workspace
  rug_ecr_image               = local.rug_ecr_image
  autoscaling_enabled         = local.env_config.locals.autoscaling_enabled
  s3_bucket_artifacts         = local.env_config.locals.s3_bucket_artifacts 
  redis_subnet_group_name     = local.env_config.locals.redis_subnet_group_name 
  redis_node_type             = local.env_config.locals.redis_node_type
  automatic_failover_enabled  = local.env_config.locals.automatic_failover_enabled
  num_cache_clusters          = local.env_config.locals.num_cache_clusters
}