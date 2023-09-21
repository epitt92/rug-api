resource "aws_ses_domain_identity" "domain" {
  domain = "rug.ai"
}

resource "aws_ses_domain_dkim" "domain_dkim" {
  domain = "${aws_ses_domain_identity.domain.domain}"
}

resource "aws_cognito_user_pool" "user_pool" {
  name = "${var.stage}-${var.workspace}-user-pool"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  password_policy {
    minimum_length    = 10
    require_lowercase = false
    require_numbers   = false
    require_symbols   = false
    require_uppercase = false
  }

  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "Account Confirmation"
    email_message        = "Your confirmation code is {####}"
  }

#   email_configuration {
#     email_sending_account = "DEVELOPER"
#     source_arn            = "{{SES_EMAIL_ARN}}"
#   }

  email_configuration {
    email_sending_account = "DEVELOPER"
    from_email_address    = "no-reply@${aws_ses_domain_identity.domain.domain}"
    source_arn            = aws_ses_domain_identity.domain.arn
  }
  
  lambda_config {
    custom_message = aws_lambda_function.cognito_custom_message_lambda.arn
  }

  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "email"
    required                 = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }
}

resource "aws_cognito_user_pool_client" "client" {
  name = "${var.stage}-${var.workspace}-cognito-client"

  user_pool_id                  = aws_cognito_user_pool.user_pool.id
  generate_secret               = false
  refresh_token_validity        = 90
  prevent_user_existence_errors = "ENABLED"
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]

}

/// cognito user pool without email verification
///
resource "aws_cognito_user_pool" "user_pool_no_email_verification" {
  name = "${var.stage}-${var.workspace}-user-pool-no-email-verification"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]  # This line will auto-verify email after signup

  password_policy {
    minimum_length    = 10
    require_lowercase = false
    require_numbers   = false
    require_symbols   = false
    require_uppercase = false
  }

  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "email"
    required                 = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

}

resource "aws_cognito_user_pool_client" "client-no-email-verification" {
  name = "${var.stage}-${var.workspace}-cognito-client"

  user_pool_id                  = aws_cognito_user_pool.user_pool_no_email_verification.id
  generate_secret               = false
  refresh_token_validity        = 90
  prevent_user_existence_errors = "ENABLED"
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_ADMIN_USER_PASSWORD_AUTH"
  ]
}