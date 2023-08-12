locals {
  environment                                       = "dev"
  aws_region                                        = "eu-west-2"
  account_id                                        = "701199753814"    
  project_name                                      = "rug" 
  stage                                             = "dev"
  backend                                           = "s3"
  bucket                                            = "${local.project_name}-${local.stage}-${local.account_id}-terraform-states-bucket"
  key                                               = "global/s3"
  region                                            = "eu-west-2"
  encrypt                                           = true
  dynamodb_table                                    = "dynamodb-state-locking"
  autoscaling_enabled                               = false
  tags                                              = {
    Stage     = "${local.stage}"    
    Cloud     = "aws"           
  }

}