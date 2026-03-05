# infrastructure/environments/shared/outputs.tf
# ─────────────────────────────────────────────────────────────
# stg / prod の Terraform root が data source で参照する値を出力。
# terraform output で確認するか、stg/prod の variables.tfvars に転記する。
# ─────────────────────────────────────────────────────────────

output "vpc_id" {
  description = "共有 VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_name" {
  description = "共有 VPC 名（stg/prod の data source フィルタに使用）"
  value       = "${var.project_name}-shared-vpc"
}

# stg サブネット（VPC module の index 0-1）
output "stg_public_subnet_ids" {
  description = "stg 用パブリックサブネット ID（ALB 配置先）"
  value       = slice(module.vpc.public_subnets, 0, 2)
}

output "stg_private_subnet_ids" {
  description = "stg 用プライベートサブネット ID（ECS / RDS 配置先）"
  value       = slice(module.vpc.private_subnets, 0, 2)
}

# prod サブネット（VPC module の index 2-3）
output "prod_public_subnet_ids" {
  description = "prod 用パブリックサブネット ID（ALB 配置先）"
  value       = slice(module.vpc.public_subnets, 2, 4)
}

output "prod_private_subnet_ids" {
  description = "prod 用プライベートサブネット ID（ECS / RDS 配置先）"
  value       = slice(module.vpc.private_subnets, 2, 4)
}

output "ecr_repository_url" {
  description = "ECR リポジトリ URL（CD パイプラインで使用）"
  value       = aws_ecr_repository.backend.repository_url
}

output "cat_photos_bucket_name" {
  description = "猫写真 S3 バケット名"
  value       = aws_s3_bucket.cat_photos.id
}

output "cloudfront_domain_name" {
  description = "CloudFront ドメイン名（猫写真 CDN URL）"
  value       = aws_cloudfront_distribution.cat_photos.domain_name
}

# ─────────────────────────────────────────────────────────────
# GitHub Actions OIDC Role ARNs
# ─────────────────────────────────────────────────────────────

output "github_actions_stg_role_arn" {
  description = "GitHub Actions stg デプロイ用 IAM Role ARN"
  value       = aws_iam_role.github_actions_stg.arn
}

output "github_actions_prod_role_arn" {
  description = "GitHub Actions prod デプロイ用 IAM Role ARN"
  value       = aws_iam_role.github_actions_prod.arn
}
