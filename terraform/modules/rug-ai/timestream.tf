resource "aws_timestreamwrite_database" "db" {
  database_name = "rug_api_db"
}

resource "aws_timestreamwrite_table" "event_logs_table" {
  database_name = aws_timestreamwrite_database.db.database_name
  table_name    = "eventlogs"
}

resource "aws_timestreamwrite_table" "review_logs_table" {
  database_name = aws_timestreamwrite_database.db.database_name
  table_name    = "reviewlogs"
}
