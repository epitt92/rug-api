resource "aws_dynamodb_table" "rug_token_metrics_table" {
  name         = "tokenmetrics"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "address_id"
  range_key      = "timestamp"

  attribute {
    name = "address_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "N"
  }
}

resource "aws_dynamodb_table" "rug_supply_reports_table" {
  name         = "supplyreports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "address_id"
  range_key      = "timestamp"

  attribute {
    name = "address_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "N"
  }
}

resource "aws_dynamodb_table" "rug_transfer_rability_reports_table" {
  name         = "transferrabilityreports"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "address_id"
  range_key      = "timestamp"

  attribute {
    name = "address_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "N"
  }
}


resource "aws_dynamodb_table" "rugsource_code_table" {
  name         = "sourcecode"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "address_id"

  attribute {
    name = "address_id"
    type = "S"
  }

}

resource "aws_dynamodb_table" "feeds_table" {
  name         = "feeds"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "feedtype"
  range_key      = "timestamp"

  attribute {
    name = "feedtype"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "N"
  }
}


resource "aws_dynamodb_table" "rug_users_table" {
  name         = "users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "username"

  attribute {
    name = "username"
    type = "S"
  }

}

resource "aws_dynamodb_table" "rug_referralcodes_table" {
  name         = "referralcodes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "referral_code"
  range_key      = "timestamp"

  attribute {
    name = "referral_code"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "N"
  }
}
