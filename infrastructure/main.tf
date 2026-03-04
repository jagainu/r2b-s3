# infrastructure/main.tf
# ─────────────────────────────────────────────────────────────
# クラウド構成図（cloud-diagram.drawio）に基づく AWS インフラ定義
#
# 構成概要:
#   - 同一 VPC 内に stg / prod サブネットを分離（コスト最適化）
#   - パブリックサブネット: ALB（各環境）
#   - プライベートサブネット: ECS Fargate + RDS PostgreSQL（各環境）
#   - ECR: stg/prod 共用（image_tag で環境を区別）
#   - S3 + CloudFront: 猫写真配信（stg/prod 共用）
# ─────────────────────────────────────────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "Terraform"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ─────────────────────────────────────────────────────────────
# VPC（stg/prod 共用。サブネットで環境分離）
# drawio: "AWS VPC（同一VPC: stg/prod サブネット分離）"
# ─────────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-shared"
  cidr = var.vpc_cidr

  # 2 AZ を使用
  azs = slice(data.aws_availability_zones.available.names, 0, 2)

  # stg サブネット + prod サブネット（計 4 パブリック + 4 プライベート）
  public_subnets  = concat(var.stg_public_subnets, var.prod_public_subnets)
  private_subnets = concat(var.stg_private_subnets, var.prod_private_subnets)

  enable_nat_gateway     = true
  single_nat_gateway     = true  # コスト削減。prod で冗長化する場合は false に変更
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # サブネットのタグで stg/prod を区別する
  public_subnet_tags = {
    "Tier" = "public"
  }
  private_subnet_tags = {
    "Tier" = "private"
  }

  tags = {
    Name = "${var.project_name}-shared-vpc"
  }
}

# ─────────────────────────────────────────────────────────────
# ECR（stg/prod 共用。image_tag で環境を区別する）
# drawio: ECR（コンテナレジストリ）
# ─────────────────────────────────────────────────────────────
resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-backend-ecr"
  }
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "古いイメージを自動削除（最新${var.ecr_image_keep_count}件を保持）"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = var.ecr_image_keep_count
      }
      action = { type = "expire" }
    }]
  })
}

# ─────────────────────────────────────────────────────────────
# S3（猫写真ストレージ。stg/prod 共用）
# drawio: S3（猫写真ストレージ）
# ─────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "cat_photos" {
  bucket = var.cat_photos_bucket_name

  tags = {
    Name = "${var.project_name}-cat-photos"
  }
}

resource "aws_s3_bucket_public_access_block" "cat_photos" {
  bucket = aws_s3_bucket.cat_photos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "cat_photos" {
  bucket = aws_s3_bucket.cat_photos.id
  versioning_configuration {
    status = "Enabled"
  }
}

# CloudFront OAC（S3 へのアクセスを CloudFront 経由のみに制限）
resource "aws_cloudfront_origin_access_control" "cat_photos" {
  name                              = "${var.project_name}-cat-photos-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_s3_bucket_policy" "cat_photos" {
  bucket = aws_s3_bucket.cat_photos.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudFrontServicePrincipal"
      Effect = "Allow"
      Principal = {
        Service = "cloudfront.amazonaws.com"
      }
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.cat_photos.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.cat_photos.arn
        }
      }
    }]
  })
}

# ─────────────────────────────────────────────────────────────
# CloudFront（猫写真 CDN）
# drawio: CloudFront（猫写真CDN）
# ─────────────────────────────────────────────────────────────
resource "aws_cloudfront_distribution" "cat_photos" {
  enabled             = true
  comment             = "${var.project_name} 猫写真 CDN"
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.cat_photos.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.cat_photos.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.cat_photos.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.cat_photos.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400   # 1日
    max_ttl     = 31536000 # 1年
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    # TODO: 独自ドメインを使う場合は以下を設定する
    # acm_certificate_arn      = "TODO: ACM 証明書 ARN（us-east-1 リージョン）"
    # ssl_support_method       = "sni-only"
    # minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name = "${var.project_name}-cat-photos-cdn"
  }
}

# ─────────────────────────────────────────────────────────────
# セキュリティグループ
# ─────────────────────────────────────────────────────────────

# ALB 用 SG（stg）
resource "aws_security_group" "stg_alb" {
  name        = "${var.project_name}-stg-alb-sg"
  description = "stg ALB Security Group"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-stg-alb-sg" }
}

# ECS 用 SG（stg）
resource "aws_security_group" "stg_ecs" {
  name        = "${var.project_name}-stg-ecs-sg"
  description = "stg ECS Security Group"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.stg_alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-stg-ecs-sg" }
}

# RDS 用 SG（stg）
resource "aws_security_group" "stg_rds" {
  name        = "${var.project_name}-stg-rds-sg"
  description = "stg RDS Security Group"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.stg_ecs.id]
  }

  tags = { Name = "${var.project_name}-stg-rds-sg" }
}

# ALB 用 SG（prod）
resource "aws_security_group" "prod_alb" {
  name        = "${var.project_name}-prod-alb-sg"
  description = "prod ALB Security Group"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-prod-alb-sg" }
}

# ECS 用 SG（prod）
resource "aws_security_group" "prod_ecs" {
  name        = "${var.project_name}-prod-ecs-sg"
  description = "prod ECS Security Group"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.prod_alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-prod-ecs-sg" }
}

# RDS 用 SG（prod）
resource "aws_security_group" "prod_rds" {
  name        = "${var.project_name}-prod-rds-sg"
  description = "prod RDS Security Group"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.prod_ecs.id]
  }

  tags = { Name = "${var.project_name}-prod-rds-sg" }
}

# ─────────────────────────────────────────────────────────────
# RDS DB Subnet Group
# ─────────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "stg" {
  name       = "${var.project_name}-stg-db-subnet-group"
  subnet_ids = slice(module.vpc.private_subnets, 0, 2) # stg 用プライベートサブネット

  tags = { Name = "${var.project_name}-stg-db-subnet-group" }
}

resource "aws_db_subnet_group" "prod" {
  name       = "${var.project_name}-prod-db-subnet-group"
  subnet_ids = slice(module.vpc.private_subnets, 2, 4) # prod 用プライベートサブネット

  tags = { Name = "${var.project_name}-prod-db-subnet-group" }
}

# ─────────────────────────────────────────────────────────────
# ALB（stg）
# drawio: ALB（Application Load Balancer）
# ─────────────────────────────────────────────────────────────
module "stg_alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name    = "${var.project_name}-stg-alb"
  vpc_id  = module.vpc.vpc_id
  subnets = slice(module.vpc.public_subnets, 0, 2) # stg 用パブリックサブネット

  security_groups = [aws_security_group.stg_alb.id]

  target_groups = {
    backend = {
      name             = "${var.project_name}-stg-tg"
      protocol         = "HTTP"
      port             = 8000
      target_type      = "ip"
      health_check = {
        path                = "/api/v1/health"
        healthy_threshold   = 2
        unhealthy_threshold = 3
        interval            = 30
      }
    }
  }

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"
      forward  = { target_group_key = "backend" }
      # TODO: HTTPS を使う場合は以下に変更する
      # redirect = {
      #   port        = "443"
      #   protocol    = "HTTPS"
      #   status_code = "HTTP_301"
      # }
    }
    # TODO: HTTPS リスナーを追加する場合
    # https = {
    #   port            = 443
    #   protocol        = "HTTPS"
    #   certificate_arn = "TODO: ACM 証明書 ARN"
    #   forward         = { target_group_key = "backend" }
    # }
  }

  tags = { Environment = "stg" }
}

# ─────────────────────────────────────────────────────────────
# ALB（prod）
# ─────────────────────────────────────────────────────────────
module "prod_alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name    = "${var.project_name}-prod-alb"
  vpc_id  = module.vpc.vpc_id
  subnets = slice(module.vpc.public_subnets, 2, 4) # prod 用パブリックサブネット

  security_groups = [aws_security_group.prod_alb.id]

  target_groups = {
    backend = {
      name             = "${var.project_name}-prod-tg"
      protocol         = "HTTP"
      port             = 8000
      target_type      = "ip"
      health_check = {
        path                = "/api/v1/health"
        healthy_threshold   = 2
        unhealthy_threshold = 3
        interval            = 30
      }
    }
  }

  listeners = {
    http = {
      port     = 80
      protocol = "HTTP"
      forward  = { target_group_key = "backend" }
    }
  }

  tags = { Environment = "prod" }
}

# ─────────────────────────────────────────────────────────────
# ECS（stg）
# drawio: ECS Fargate（FastAPI Python 3.11）
# ─────────────────────────────────────────────────────────────
module "stg_ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 5.0"

  cluster_name = "${var.project_name}-stg-cluster"

  services = {
    backend = {
      cpu    = var.stg_ecs_cpu
      memory = var.stg_ecs_memory

      container_definitions = {
        backend = {
          image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
          essential = true

          port_mappings = [{
            container_port = 8000
            protocol       = "tcp"
          }]

          environment = [
            { name = "ENVIRONMENT", value = "stg" },
            # TODO: terraform apply 後に以下を stg_rds_endpoint で更新する
            # { name = "DATABASE_URL", value = "postgresql+asyncpg://user:pass@{stg_rds_endpoint}/app_stg" }
          ]

          log_configuration = {
            log_driver = "awslogs"
            options = {
              awslogs-group         = "/ecs/${var.project_name}-stg-backend"
              awslogs-region        = var.aws_region
              awslogs-stream-prefix = "ecs"
            }
          }
        }
      }

      load_balancer = {
        service = {
          target_group_arn = module.stg_alb.target_groups["backend"].arn
          container_name   = "backend"
          container_port   = 8000
        }
      }

      subnet_ids         = slice(module.vpc.private_subnets, 0, 2) # stg 用プライベートサブネット
      security_group_ids = [aws_security_group.stg_ecs.id]
      assign_public_ip   = false
    }
  }

  tags = { Environment = "stg" }
}

# ─────────────────────────────────────────────────────────────
# ECS（prod）
# ─────────────────────────────────────────────────────────────
module "prod_ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 5.0"

  cluster_name = "${var.project_name}-prod-cluster"

  services = {
    backend = {
      cpu    = var.prod_ecs_cpu
      memory = var.prod_ecs_memory

      container_definitions = {
        backend = {
          image     = "${aws_ecr_repository.backend.repository_url}:${var.image_tag}"
          essential = true

          port_mappings = [{
            container_port = 8000
            protocol       = "tcp"
          }]

          environment = [
            { name = "ENVIRONMENT", value = "prod" },
            # TODO: terraform apply 後に以下を prod_rds_endpoint で更新する
            # { name = "DATABASE_URL", value = "postgresql+asyncpg://user:pass@{prod_rds_endpoint}/app_prod" }
          ]

          log_configuration = {
            log_driver = "awslogs"
            options = {
              awslogs-group         = "/ecs/${var.project_name}-prod-backend"
              awslogs-region        = var.aws_region
              awslogs-stream-prefix = "ecs"
            }
          }
        }
      }

      load_balancer = {
        service = {
          target_group_arn = module.prod_alb.target_groups["backend"].arn
          container_name   = "backend"
          container_port   = 8000
        }
      }

      subnet_ids         = slice(module.vpc.private_subnets, 2, 4) # prod 用プライベートサブネット
      security_group_ids = [aws_security_group.prod_ecs.id]
      assign_public_ip   = false
    }
  }

  tags = { Environment = "prod" }
}

# ─────────────────────────────────────────────────────────────
# RDS（stg）
# drawio: RDS PostgreSQL（stg）
# ─────────────────────────────────────────────────────────────
module "stg_rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-stg-db"

  engine         = "postgres"
  engine_version = "15"
  instance_class = var.stg_rds_instance_class
  family         = "postgres15"

  db_name  = var.stg_db_name
  username = var.stg_db_username

  # パスワードは AWS が自動生成・Secrets Manager に保存（ユーザーが入力しない）
  manage_master_user_password = true

  vpc_security_group_ids = [aws_security_group.stg_rds.id]
  db_subnet_group_name   = aws_db_subnet_group.stg.name

  # stg は Single-AZ でコスト削減
  multi_az = false

  storage_type          = "gp3"
  allocated_storage     = 20
  max_allocated_storage = 100 # ストレージオートスケーリング上限（GB）

  skip_final_snapshot = true  # stg は削除時のスナップショット不要
  deletion_protection = false

  tags = { Environment = "stg" }
}

# ─────────────────────────────────────────────────────────────
# RDS（prod）
# drawio: RDS PostgreSQL（prod・Multi-AZ）
# ─────────────────────────────────────────────────────────────
module "prod_rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-prod-db"

  engine         = "postgres"
  engine_version = "15"
  instance_class = var.prod_rds_instance_class
  family         = "postgres15"

  db_name  = var.prod_db_name
  username = var.prod_db_username

  # パスワードは AWS が自動生成・Secrets Manager に保存
  manage_master_user_password = true

  vpc_security_group_ids = [aws_security_group.prod_rds.id]
  db_subnet_group_name   = aws_db_subnet_group.prod.name

  # prod は Multi-AZ 有効（drawio 仕様・SLA 99.9% 達成のため）
  multi_az = true

  storage_type          = "gp3"
  allocated_storage     = 20
  max_allocated_storage = 500 # 本番はオートスケーリング上限を大きく設定

  skip_final_snapshot = false # prod は削除時にスナップショットを保存する
  deletion_protection = true  # 誤削除防止

  tags = { Environment = "prod" }
}

# ─────────────────────────────────────────────────────────────
# CloudWatch Logs（ECS ログ）
# ─────────────────────────────────────────────────────────────
resource "aws_cloudwatch_log_group" "stg_backend" {
  name              = "/ecs/${var.project_name}-stg-backend"
  retention_in_days = 30

  tags = { Environment = "stg" }
}

resource "aws_cloudwatch_log_group" "prod_backend" {
  name              = "/ecs/${var.project_name}-prod-backend"
  retention_in_days = 90 # prod はログを長期保持

  tags = { Environment = "prod" }
}
