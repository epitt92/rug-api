
include {
  path = find_in_parent_folders("terragrunt.hcl")
}

locals {
  source      = get_env("TG_ENV", "dev")
  workspace   = get_env("TG_WORKSPACE", "default")
  env_config  = read_terragrunt_config(find_in_parent_folders("config/${local.source}.hcl"))
  rug_ecr_image = get_env("TG_RUG_ECR_IMAGE", "701199753814.dkr.ecr.eu-west-2.amazonaws.com/dev-default-rug-app:latest")

}

terraform {
  source = "${get_parent_terragrunt_dir()}/modules/rug-ai"
}

inputs = {
  region                 = local.env_config.locals.aws_region
  account_id             = local.env_config.locals.account_id
  stage                  = local.env_config.locals.stage
  tags                   = local.env_config.locals.tags
  workspace              = local.workspace
  rug_ecr_image          = local.rug_ecr_image
  autoscaling_enabled    = local.env_config.locals.autoscaling_enabled

}