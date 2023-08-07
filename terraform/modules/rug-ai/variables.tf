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