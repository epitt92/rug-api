resource "aws_secretsmanager_secret" "ETHEREUM_BLOCK_EXPLORER_API_KEY" {
  name = "ETHEREUM_BLOCK_EXPLORER_API_KEY"
}

resource "aws_secretsmanager_secret" "ARBITRUM_BLOCK_EXPLORER_API_KEY" {
  name = "ARBITRUM_BLOCK_EXPLORER_API_KEY"
}

resource "aws_secretsmanager_secret" "BASE_BLOCK_EXPLORER_API_KEY" {
  name = "BASE_BLOCK_EXPLORER_API_KEY"
}

resource "aws_secretsmanager_secret" "BNB_BLOCK_EXPLORER_API_KEY" {
  name = "BNB_BLOCK_EXPLORER_API_KEY"
}

resource "aws_secretsmanager_secret" "ETHEREUM_RPC_URL" {
  name = "ETHEREUM_RPC_URL"
}

resource "aws_secretsmanager_secret" "ARBITRUM_RPC_URL" {
  name = "ARBITRUM_RPC_URL"
}

resource "aws_secretsmanager_secret" "BASE_RPC_URL" {
  name = "BASE_RPC_URL"
}
