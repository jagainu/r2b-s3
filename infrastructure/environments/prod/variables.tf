# infrastructure/environments/prod/variables.tf

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

variable "image_tag" {
  description = "デプロイする Docker イメージタグ（CD パイプラインが TF_VAR_image_tag で注入）"
  type        = string
  default     = "latest"
}

# ─── shared から参照するサブネット CIDR ────────────────────

variable "prod_public_subnet_cidrs" {
  description = "prod パブリックサブネット CIDR（shared の VPC から検索するために使用）"
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.101.0/24"]
}

variable "prod_private_subnet_cidrs" {
  description = "prod プライベートサブネット CIDR（shared の VPC から検索するために使用）"
  type        = list(string)
  default     = ["10.0.110.0/24", "10.0.111.0/24"]
}

# ─── ECS ───────────────────────────────────────────────────
variable "ecs_cpu" {
  description = "ECS タスクの CPU ユニット数"
  type        = number
  default     = 512
}

variable "ecs_memory" {
  description = "ECS タスクのメモリ（MB）"
  type        = number
  default     = 1024
}

# ─── RDS ───────────────────────────────────────────────────
variable "rds_instance_class" {
  description = "RDS インスタンスタイプ（Multi-AZ 有効）"
  type        = string
  default     = "db.t3.small"
}

variable "db_name" {
  description = "データベース名"
  type        = string
  default     = "catbreed_prod"
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  default     = "catbreed"
}
