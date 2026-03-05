# infrastructure/environments/shared/variables.tf

variable "project_name" {
  description = "プロジェクト名（リソース命名プレフィックス）"
  type        = string
  default     = "r2b"
}

variable "aws_region" {
  description = "AWS リージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "vpc_cidr" {
  description = "VPC CIDR ブロック"
  type        = string
  default     = "10.0.0.0/16"
}

variable "stg_public_subnets" {
  description = "stg 用パブリックサブネット CIDR（ALB 配置先）。2 AZ 分"
  type        = list(string)
  default     = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "stg_private_subnets" {
  description = "stg 用プライベートサブネット CIDR（ECS / RDS 配置先）。2 AZ 分"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "prod_public_subnets" {
  description = "prod 用パブリックサブネット CIDR（ALB 配置先）。2 AZ 分"
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.101.0/24"]
}

variable "prod_private_subnets" {
  description = "prod 用プライベートサブネット CIDR（ECS / RDS 配置先）。2 AZ 分"
  type        = list(string)
  default     = ["10.0.110.0/24", "10.0.111.0/24"]
}

variable "ecr_image_keep_count" {
  description = "ECR に保持するイメージ数"
  type        = number
  default     = 10
}

variable "cat_photos_bucket_name" {
  description = "猫写真ストレージ S3 バケット名（グローバルで一意）"
  type        = string
  default     = "r2b-cat-photos"
}
