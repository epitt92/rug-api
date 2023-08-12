locals {
  environment                                       = "stage"
  aws_region                                        = "eu-west-2"
  account_id                                        = "454343598698"    
  project_name                                      = "rug" 
  stage                                             = "stage"
  backend                                           = "s3"
  bucket                                            = "${local.project_name}-${local.stage}-${local.account_id}-terraform-states-bucket"
  key                                               = "global/s3"
  region                                            = "eu-west-2"
  encrypt                                           = true
  dynamodb_table                                    = "dynamodb-state-locking"
  autoscaling_enabled                               = true
  tags                                              = {
    Stage     = "${local.stage}"    
    Cloud     = "aws"           
  }

}