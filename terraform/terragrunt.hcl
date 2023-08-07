locals {
  env         = get_env("TG_ENV", "stage")
  workspace   = get_env("TG_WORKSPACE", "default")
  env_config  = read_terragrunt_config(find_in_parent_folders("config/${local.env}.hcl"))
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOF
    provider "aws" {
    region = "${local.env_config.locals.region}"
    }
    EOF
}

remote_state {
  backend = "s3"
  config = {
    bucket         = "${local.env_config.locals.bucket}"
    key            = "${local.env_config.locals.key}/${path_relative_to_include()}"
    region         = "${local.env_config.locals.region}"
    dynamodb_table = "${local.env_config.locals.dynamodb_table}"
    encrypt        = true
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}