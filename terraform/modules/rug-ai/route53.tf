resource "aws_route53_zone" "primary" {
  name = "${var.stage}.api.rug.ai"
}

resource "aws_route53_record" "rug_ai" {
  zone_id = aws_route53_zone.primary.zone_id
  name    = "${var.stage}.api.rug.ai"
  type    = "A"

  alias {
    name                   = aws_alb.rug_ai.dns_name
    zone_id                = aws_alb.rug_ai.zone_id
    evaluate_target_health = true
  }
}



resource "aws_acm_certificate" "cert" {
  domain_name       = "${var.stage}.api.rug.ai"
  validation_method = "DNS"

  tags = {
    Environment = var.stage
  }

}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.primary.zone_id
}