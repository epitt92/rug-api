data "aws_vpc" "vpc" {
  filter {
    name   = "tag:Cloud"
    values = ["aws"]
  }
  tags = {
    Stage = "${var.stage}"
  }
}


data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.vpc.id]
  }

  tags = {
    Attributes = "public"
  }
}

resource "aws_security_group" "rug_ai" {
  name        = "${var.stage}-${var.workspace}-rug-ai"
  description = "Allow traffic to and from the Load Balancer"
  vpc_id      = data.aws_vpc.vpc.id
  ingress {
    description     = "Allow 443 (HTTPS) from Everywhere to LoadBalancer"
    protocol        = "tcp"
    from_port       = 443
    to_port         = 443
    cidr_blocks     = ["0.0.0.0/0"]
    prefix_list_ids = []
  }
  ingress {
    description      = "Allow 80 (HTTP) from Everywhere to LoadBalancer" # this is temperory until we create TLS certificate
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  egress {
    description = "Allow Everything from LoadBalancer to Everywhere"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  lifecycle {
    create_before_destroy = true
  }
  timeouts {
    delete = "5m"
  }
  tags = {
    Name    = "${var.stage} ${var.workspace} rug ai lb sg"
    Account = var.account_id
  }
}

resource "aws_alb" "rug_ai" {
  name            = "${var.stage}-${var.workspace}-rug-ai"
  internal        = false
  security_groups = [aws_security_group.rug_ai.id]
  subnets         = toset(data.aws_subnets.public.ids)
  idle_timeout    = 180 
  #   access_logs {
  #     bucket  = module.s3_bucket_alb_logging.bucket_name
  #     enabled = true
  #   }
  tags = {
    Name    = "${var.stage}-${var.workspace}-rug-ai ALB"
    Account = var.account_id
  }
}
