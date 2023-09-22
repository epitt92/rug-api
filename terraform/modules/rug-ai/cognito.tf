resource "aws_ses_domain_identity" "domain" {
  domain = "rug.ai"
}

resource "aws_ses_domain_dkim" "domain_dkim" {
  domain = "${aws_ses_domain_identity.domain.domain}"
}
