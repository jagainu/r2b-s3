# infrastructure/environments/stg/variables.tf

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
# shared/ で作成したサブネットを CIDR で特定するために使用する

variable "stg_public_subnet_cidrs" {
  description = "stg パブリックサブネット CIDR（shared の VPC から検索するために使用）"
  type        = list(string)
  default     = ["10.0.0.0/24", "10.0.1.0/24"]
}

variable "stg_private_subnet_cidrs" {
  description = "stg プライベートサブネット CIDR（shared の VPC から検索するために使用）"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

# ─── ECS ───────────────────────────────────────────────────
variable "ecs_cpu" {
  description = "ECS タスクの CPU ユニット数"
  type        = number
  default     = 256
}

variable "ecs_memory" {
  description = "ECS タスクのメモリ（MB）"
  type        = number
  default     = 512
}

# ─── RDS ───────────────────────────────────────────────────
variable "rds_instance_class" {
  description = "RDS インスタンスタイプ"
  type        = string
  default     = "db.t3.micro"
}

variable "db_name" {
  description = "データベース名"
  type        = string
  default     = "catbreed_stg"
}

variable "db_username" {
  description = "データベースユーザー名"
  type        = string
  default     = "catbreed"
}

variable "db_password" {
  description = "データベースパスワード（TF_VAR_db_password で注入する。Git には含めない）"
  type        = string
  sensitive   = true
}
