# infrastructure/environments/prod/terraform.tfvars
# ─────────────────────────────────────────────────────────────
# prod 環境の変数値
#
# 実行方法（このディレクトリから）:
#   cp backend.tf.example backend.tf
#   terraform init
#   terraform apply
# ─────────────────────────────────────────────────────────────

project_name = "r2b"
aws_region   = "ap-northeast-1"

# shared/ で作成したサブネットを CIDR で特定する
prod_public_subnet_cidrs  = ["10.0.100.0/24", "10.0.101.0/24"]
prod_private_subnet_cidrs = ["10.0.110.0/24", "10.0.111.0/24"]

# ECS: prod は余裕を持って 512/1024
ecs_cpu    = 512
ecs_memory = 1024

# RDS: prod は Multi-AZ 有効（main.tf 側で設定済み）
rds_instance_class = "db.t3.small"
db_name            = "catbreed_prod"
db_username        = "catbreed"

# image_tag は CD パイプラインが TF_VAR_image_tag=<git-sha> で注入する
# image_tag = "latest"
