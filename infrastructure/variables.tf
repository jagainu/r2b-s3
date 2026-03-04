# infrastructure/variables.tf
# ─────────────────────────────────────────────────────────────
# 共通変数定義
# 具体的な値は environments/stg/terraform.tfvars または
#              environments/prod/terraform.tfvars で設定する
# ─────────────────────────────────────────────────────────────

variable "project_name" {
  description = "プロジェクト名（リソース命名プレフィックスになります）"
  type        = string
  default     = "r2b"
}

variable "aws_region" {
  description = "AWS リージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "image_tag" {
  description = "デプロイする Docker イメージのタグ（CD パイプラインが git SHA を TF_VAR_image_tag で注入する）"
  type        = string
  default     = "latest" # ローカル動作確認のみ。本番 CD では TF_VAR_image_tag で上書きされる
}

# ─── VPC ───────────────────────────────────────────────────
variable "vpc_cidr" {
  description = "VPC CIDR ブロック。stg/prod が同一 VPC 内に収まるように設計する"
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

# ─── ECR ───────────────────────────────────────────────────
variable "ecr_image_keep_count" {
  description = "ECR に保持するイメージ数（古いイメージを自動削除）"
  type        = number
  default     = 10
}

# ─── ECS (stg) ─────────────────────────────────────────────
variable "stg_ecs_cpu" {
  description = "stg ECS タスクの CPU ユニット数（256 / 512 / 1024 / 2048）"
  type        = number
  default     = 256
}

variable "stg_ecs_memory" {
  description = "stg ECS タスクのメモリ（MB）（512 / 1024 / 2048 / 4096）"
  type        = number
  default     = 512
}

# ─── ECS (prod) ─────────────────────────────────────────────
variable "prod_ecs_cpu" {
  description = "prod ECS タスクの CPU ユニット数（256 / 512 / 1024 / 2048）"
  type        = number
  default     = 512
}

variable "prod_ecs_memory" {
  description = "prod ECS タスクのメモリ（MB）（512 / 1024 / 2048 / 4096）"
  type        = number
  default     = 1024
}

# ─── RDS (stg) ─────────────────────────────────────────────
variable "stg_rds_instance_class" {
  description = "stg RDS インスタンスタイプ"
  type        = string
  default     = "db.t3.micro"
}

variable "stg_db_name" {
  description = "stg データベース名"
  type        = string
  default     = "catbreed_stg"
}

variable "stg_db_username" {
  description = "stg データベースユーザー名"
  type        = string
  default     = "catbreed"
}

# ─── RDS (prod) ─────────────────────────────────────────────
variable "prod_rds_instance_class" {
  description = "prod RDS インスタンスタイプ（Multi-AZ 有効）"
  type        = string
  default     = "db.t3.small"
}

variable "prod_db_name" {
  description = "prod データベース名"
  type        = string
  default     = "catbreed_prod"
}

variable "prod_db_username" {
  description = "prod データベースユーザー名"
  type        = string
  default     = "catbreed"
}

# ─── S3 (猫写真) ───────────────────────────────────────────
variable "cat_photos_bucket_name" {
  description = "猫写真ストレージ S3 バケット名（グローバルで一意）"
  type        = string
  default     = "r2b-cat-photos"
}
