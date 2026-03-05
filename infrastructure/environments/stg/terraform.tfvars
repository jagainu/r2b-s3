# infrastructure/environments/stg/terraform.tfvars
# ─────────────────────────────────────────────────────────────
# stg 環境の変数値
#
# 実行方法（このディレクトリから）:
#   cp backend.tf.example backend.tf
#   terraform init
#   terraform apply
# ─────────────────────────────────────────────────────────────

project_name = "r2b"
aws_region   = "ap-northeast-1"

# shared/ で作成したサブネットを CIDR で特定する
stg_public_subnet_cidrs  = ["10.0.0.0/24", "10.0.1.0/24"]
stg_private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]

# ECS: DAU 1,000・50 RPS の規模感では 256/512 で十分
ecs_cpu    = 256
ecs_memory = 512

# RDS: stg は Single-AZ でコスト削減
rds_instance_class = "db.t3.micro"
db_name            = "catbreed_stg"
db_username        = "catbreed"

# image_tag は CD パイプラインが TF_VAR_image_tag=<git-sha> で注入する
# image_tag = "latest"
