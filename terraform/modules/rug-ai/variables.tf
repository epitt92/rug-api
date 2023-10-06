variable "account_id" {
  description = "The Deployment account id"
}

variable "stage" {
  description = "The Deployment stage"
}

variable "tags" {
  description = "The tags for aws resources"
}

variable "region" {
  description = "The aws region"
}

variable "workspace" {
  description = "The Deployment workspace"
}

variable "rug_ecr_image" {
  description = "The rug ecr image"
}

variable "autoscaling_enabled" {
  description = "The autoscaling enabled"
}

variable "s3_bucket_artifacts" {
  description = "The s3 bucket artifacts"
}

variable "redis_subnet_group_name" {
  description = "The redis subnet group name"
}

variable "redis_node_type" {
  description = "The redis node type"
}

variable "automatic_failover_enabled" {
  description = "The automatic failover enabled"
}

variable "num_cache_clusters" {
  description = "The num cache clusters"
}