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

resource "aws_secretsmanager_secret" "RUG_API_ETHEREUM_RPC_URL" {
  name = "RUG_API_ETHEREUM_RPC_URL"
}

resource "aws_secretsmanager_secret" "RUG_API_ARBITRUM_RPC_URL" {
  name = "RUG_API_ARBITRUM_RPC_URL"
}

resource "aws_secretsmanager_secret" "RUG_API_BASE_RPC_URL" {
  name = "RUG_API_BASE_RPC_URL"
}

resource "aws_secretsmanager_secret" "GO_PLUS_APP_KEY" {
  name = "GO_PLUS_APP_KEY"
}

resource "aws_secretsmanager_secret" "GO_PLUS_APP_SECRET" {
  name = "GO_PLUS_APP_SECRET"
}
