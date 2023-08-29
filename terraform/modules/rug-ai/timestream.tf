resource "aws_timestreamwrite_database" "db" {
  provider = aws.eu-west-1
  database_name = "rug_api_db"
}

resource "aws_timestreamwrite_table" "event_logs_table" {
  provider = aws.eu-west-1
  database_name = aws_timestreamwrite_database.db.database_name
  table_name    = "eventlogs"
}

resource "aws_timestreamwrite_table" "review_logs_table" {
  provider = aws.eu-west-1
  database_name = aws_timestreamwrite_database.db.database_name
  table_name    = "reviewlogs"
}
