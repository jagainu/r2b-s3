# infrastructure/environments/prod/outputs.tf

output "alb_dns_name" {
  description = "prod ALB の DNS 名（API 接続確認・Vercel 環境変数設定に使用）"
  value       = module.alb.dns_name
}

output "ecs_cluster_name" {
  description = "prod ECS クラスター名（CD パイプラインで使用）"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "prod ECS サービス名（CD パイプラインで使用）"
  value       = try(module.ecs.services["backend"].name, "")
}

output "rds_endpoint" {
  description = "prod RDS エンドポイント（DATABASE_URL 設定に使用）"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}
