resource "aws_s3_bucket" "build_artifacts" {
  bucket    = "rug-${var.stage}-${var.account_id}-build-artifacts"
  tags      = jsondecode(var.tags)
}