# IAM role for Lambda function
resource "aws_iam_role" "cognito_custom_message_lambda_role" {
  name = "CognitoCustomMessageLambdaRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach necessary permissions to the Lambda IAM role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.cognito_custom_message_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Archive the lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "custom_message_lambda.py"
  output_path = "custom_message_lambda.zip"
}

# Lambda function resource
resource "aws_lambda_function" "cognito_custom_message_lambda" {
  filename      = data.archive_file.lambda_zip.output_path
  function_name = "CognitoCustomMessageLambda"
  role          = aws_iam_role.cognito_custom_message_lambda_role.arn
  handler       = "custom_message_lambda.lambda_handler" # Format: <FILE_NAME>.<FUNCTION_NAME>

  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.8"
}

# Lambda function permission to invoke Cognito
resource "aws_lambda_permission" "cognito_custom_message_lambda_permission" {
  statement_id  = "AllowExecutionFromCognito"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cognito_custom_message_lambda.function_name
  principal     = "cognito-idp.amazonaws.com"
}