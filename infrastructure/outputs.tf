# infrastructure/outputs.tf
# ─────────────────────────────────────────────────────────────
# 重要な値を出力。terraform apply 後に確認して CD/アプリ設定に使用する。
# ─────────────────────────────────────────────────────────────

# ─── VPC ───────────────────────────────────────────────────
output "vpc_id" {
  description = "共有 VPC ID"
  value       = module.vpc.vpc_id
}

# ─── ECR ───────────────────────────────────────────────────
output "ecr_repository_url" {
  description = "ECR リポジトリ URL（CD パイプラインで image_tag と組み合わせて push/pull に使用）"
  value       = aws_ecr_repository.backend.repository_url
}

# ─── ECS (stg) ─────────────────────────────────────────────
output "stg_alb_dns_name" {
  description = "stg ALB の DNS 名（API 接続確認・Vercel 環境変数設定に使用）"
  value       = module.stg_alb.dns_name
}

output "stg_ecs_cluster_name" {
  description = "stg ECS クラスター名（CD パイプラインで update-service に使用）"
  value       = module.stg_ecs.cluster_name
}

output "stg_ecs_service_name" {
  description = "stg ECS サービス名（CD パイプラインで update-service に使用）"
  value       = try(module.stg_ecs.services["backend"].name, "")
}

# ─── ECS (prod) ─────────────────────────────────────────────
output "prod_alb_dns_name" {
  description = "prod ALB の DNS 名（API 接続確認・Vercel 環境変数設定に使用）"
  value       = module.prod_alb.dns_name
}

output "prod_ecs_cluster_name" {
  description = "prod ECS クラスター名（CD パイプラインで update-service に使用）"
  value       = module.prod_ecs.cluster_name
}

output "prod_ecs_service_name" {
  description = "prod ECS サービス名（CD パイプラインで update-service に使用）"
  value       = try(module.prod_ecs.services["backend"].name, "")
}

# ─── RDS ───────────────────────────────────────────────────
output "stg_rds_endpoint" {
  description = "stg RDS エンドポイント（DATABASE_URL 設定に使用: terraform output stg_rds_endpoint）"
  value       = module.stg_rds.db_instance_endpoint
  sensitive   = true
}

output "prod_rds_endpoint" {
  description = "prod RDS エンドポイント（DATABASE_URL 設定に使用: terraform output prod_rds_endpoint）"
  value       = module.prod_rds.db_instance_endpoint
  sensitive   = true
}

# ─── S3 / CloudFront ───────────────────────────────────────
output "cat_photos_bucket_name" {
  description = "猫写真 S3 バケット名"
  value       = aws_s3_bucket.cat_photos.id
}

output "cloudfront_domain_name" {
  description = "CloudFront ドメイン名（猫写真 CDN URL の確認に使用）"
  value       = aws_cloudfront_distribution.cat_photos.domain_name
}
