# infrastructure/environments/stg/terraform.tfvars
# ─────────────────────────────────────────────────────────────
# stg 環境の変数値
#
# 実行方法（infrastructure/ ディレクトリから）:
#   terraform apply -var-file=environments/stg/terraform.tfvars
# ─────────────────────────────────────────────────────────────

project_name = "r2b"
aws_region   = "ap-northeast-1"

# ─── VPC / ネットワーク ───────────────────────────────────
# 同一 VPC 内に stg/prod サブネットを分離する構成
vpc_cidr = "10.0.0.0/16"

stg_public_subnets   = ["10.0.0.0/24", "10.0.1.0/24"]
stg_private_subnets  = ["10.0.10.0/24", "10.0.11.0/24"]
prod_public_subnets  = ["10.0.100.0/24", "10.0.101.0/24"]
prod_private_subnets = ["10.0.110.0/24", "10.0.111.0/24"]

# ─── ECR ──────────────────────────────────────────────────
ecr_image_keep_count = 10

# ─── ECS (stg) ────────────────────────────────────────────
# DAU 1,000・50 RPS の規模感では 256/512 で十分
stg_ecs_cpu    = 256
stg_ecs_memory = 512

# ─── ECS (prod) ───────────────────────────────────────────
# prod は余裕を持って 512/1024（Auto Scaling なし・固定スペック）
prod_ecs_cpu    = 512
prod_ecs_memory = 1024

# ─── RDS (stg) ────────────────────────────────────────────
stg_rds_instance_class = "db.t3.micro"
stg_db_name            = "catbreed_stg"
stg_db_username        = "catbreed"

# ─── RDS (prod) ───────────────────────────────────────────
# prod は Multi-AZ 有効（main.tf 側で設定済み）
prod_rds_instance_class = "db.t3.small"
prod_db_name            = "catbreed_prod"
prod_db_username        = "catbreed"

# ─── S3（猫写真） ─────────────────────────────────────────
# ⚠️ S3 バケット名はグローバルで一意。他のアカウントと被る場合は変更が必要
cat_photos_bucket_name = "r2b-cat-photos"

# image_tag は CD パイプラインが TF_VAR_image_tag=<git-sha> で注入する
# image_tag = "latest"
