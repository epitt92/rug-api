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
  s3_bucket_artifacts                               = "${local.project_name}-${local.stage}-${local.account_id}-build-artifacts"
  redis_subnet_group_name                           = "rug-api-private-redis-subnet-group"
  redis_node_type                                   = "cache.t4g.micro"
  automatic_failover_enabled                        = false
  num_cache_clusters                                = 1
  
}