module "redis" {
  source                     = "git::https://github.com/diffusion-io/rug-terraform.git//modules/redis?ref=v0.0.14"
  region                     = var.region
  stage                      = var.stage
  cluster_name               = "rug-ai-redis"
  redis_subnet_group_name    = var.redis_subnet_group_name
  redis_node_type            = var.redis_node_type
  automatic_failover_enabled = var.automatic_failover_enabled
  num_cache_clusters         = var.num_cache_clusters
  transit_encryption_enabled = true
  private                    = true
}
