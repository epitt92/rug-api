resource "aws_s3_bucket" "build_artifacts" {
  bucket    = "rug-${var.stage}-${var.account_id}-build-artifacts"
  tags      = jsondecode(var.tags)
}

resource "aws_s3_bucket" "rug_media_bucket" {
  count = var.stage == "stage" ? 1 : 0
  bucket    = "rug-${var.stage}-${var.account_id}-media"
  tags      = jsondecode(var.tags)
}

resource "aws_ssm_parameter" "rug_media_bucket_arn" {
  count = var.stage == "stage" ? 1 : 0
  name = "/s3/bucket/rug_media_bucket_arn"
  type = "String"
  value = aws_s3_bucket.rug_media_bucket[0].arn
}

# resource "aws_s3_bucket_acl" "rug_media_bucket_acl" {
#   bucket = aws_s3_bucket.rug_media_bucket[0].id
#   acl    = "public-read-write"

# }
resource "aws_s3_bucket_ownership_controls" "example" {
  count = var.stage == "stage" ? 1 : 0
  bucket = aws_s3_bucket.rug_media_bucket[0].id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_public_access_block" "example" {
  count = var.stage == "stage" ? 1 : 0
  bucket = aws_s3_bucket.rug_media_bucket[0].id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "example" {
  count = var.stage == "stage" ? 1 : 0
  depends_on = [
    aws_s3_bucket_ownership_controls.example[0],
    aws_s3_bucket_public_access_block.example[0],
  ]

  bucket = aws_s3_bucket.rug_media_bucket[0].id
  acl    = "public-read"
}

resource "aws_s3_bucket_cors_configuration" "rug_media_bucket_cors_configuration" {
  count = var.stage == "stage" ? 1 : 0
  bucket = aws_s3_bucket.rug_media_bucket[0].id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = [ 
            "DELETE",
            "GET",
            "HEAD",
            "POST",
            "PUT"
        ]
    allowed_origins = ["*"]
    expose_headers  = []
  }
}

resource "aws_s3_bucket_policy" "allow_access_to_s3" {
  count = var.stage == "stage" ? 1 : 0
  bucket = aws_s3_bucket.rug_media_bucket[0].id
  policy = data.aws_iam_policy_document.allow_access_to_s3.json
}

data "aws_iam_policy_document" "allow_access_to_s3" {
  count = var.stage == "stage" ? 1 : 0
  statement {
    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject"
    ]

    resources = [
      aws_s3_bucket.rug_media_bucket[0].arn,
      "${aws_s3_bucket.rug_media_bucket[0].arn}/*",
    ]
  }
}