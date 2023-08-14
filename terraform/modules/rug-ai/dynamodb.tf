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

