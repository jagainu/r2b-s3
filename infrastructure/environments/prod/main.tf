# infrastructure/environments/prod/main.tf
# ─────────────────────────────────────────────────────────────
# prod 専用リソース（ALB・ECS・RDS・SG・CloudWatch）
#
# 前提: environments/shared/ が apply 済みであること。
# VPC・ECR などの共有リソースは data source で参照する。
#
# 実行方法（このディレクトリから）:
#   cp backend.tf.example backend.tf
#   terraform init
#   terraform apply
# ─────────────────────────────────────────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      ManagedBy   = "Terraform"
      Environment = "prod"
    }
  }
}

# ─────────────────────────────────────────────────────────────
# 共有リソースの参照（data source）
# ─────────────────────────────────────────────────────────────

data "aws_vpc" "shared" {
  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-shared-vpc"]
  }
}

data "aws_subnets" "prod_public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.shared.id]
  }
  filter {
    name   = "cidrBlock"
    values = var.prod_public_subnet_cidrs
  }
}

data "aws_subnets" "prod_private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.shared.id]
  }
  filter {
    name   = "cidrBlock"
    values = var.prod_private_subnet_cidrs
  }
}

data "aws_ecr_repository" "backend" {
  name = "${var.project_name}-backend"
}

# ─────────────────────────────────────────────────────────────
# セキュリティグループ（prod）
# ─────────────────────────────────────────────────────────────

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-prod-alb-sg"
  description = "prod ALB Security Group"
  vpc_id      = data.aws_vpc.shared.id

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

resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-prod-ecs-sg"
  description = "prod ECS Security Group"
  vpc_id      = data.aws_vpc.shared.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-prod-ecs-sg" }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-prod-rds-sg"
  description = "prod RDS Security Group"
  vpc_id      = data.aws_vpc.shared.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }

  tags = { Name = "${var.project_name}-prod-rds-sg" }
}

# ─────────────────────────────────────────────────────────────
# RDS DB Subnet Group（prod）
# ─────────────────────────────────────────────────────────────

resource "aws_db_subnet_group" "prod" {
  name       = "${var.project_name}-prod-db-subnet-group"
  subnet_ids = data.aws_subnets.prod_private.ids

  tags = { Name = "${var.project_name}-prod-db-subnet-group" }
}

# ─────────────────────────────────────────────────────────────
# ALB（prod）
# ─────────────────────────────────────────────────────────────

module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  version = "~> 9.0"

  name    = "${var.project_name}-prod-alb"
  vpc_id  = data.aws_vpc.shared.id
  subnets = data.aws_subnets.prod_public.ids

  security_groups = [aws_security_group.alb.id]

  target_groups = {
    backend = {
      name        = "${var.project_name}-prod-tg"
      protocol    = "HTTP"
      port        = 8000
      target_type = "ip"
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
  }
}

# ─────────────────────────────────────────────────────────────
# CloudWatch Logs（prod）
# ─────────────────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project_name}-prod-backend"
  retention_in_days = 90 # prod はログを長期保持
}

# ─────────────────────────────────────────────────────────────
# ECS（prod）
# ─────────────────────────────────────────────────────────────

module "ecs" {
  source  = "terraform-aws-modules/ecs/aws"
  version = "~> 5.0"

  cluster_name = "${var.project_name}-prod-cluster"

  services = {
    backend = {
      cpu    = var.ecs_cpu
      memory = var.ecs_memory

      container_definitions = {
        backend = {
          image     = "${data.aws_ecr_repository.backend.repository_url}:${var.image_tag}"
          essential = true

          port_mappings = [{
            container_port = 8000
            protocol       = "tcp"
          }]

          environment = [
            { name = "ENVIRONMENT", value = "prod" },
            # terraform apply 後に DATABASE_URL を設定する
            # { name = "DATABASE_URL", value = "postgresql+asyncpg://user:pass@${module.rds.db_instance_address}/catbreed_prod" }
          ]

          log_configuration = {
            log_driver = "awslogs"
            options = {
              awslogs-group         = aws_cloudwatch_log_group.backend.name
              awslogs-region        = var.aws_region
              awslogs-stream-prefix = "ecs"
            }
          }
        }
      }

      load_balancer = {
        service = {
          target_group_arn = module.alb.target_groups["backend"].arn
          container_name   = "backend"
          container_port   = 8000
        }
      }

      subnet_ids         = data.aws_subnets.prod_private.ids
      security_group_ids = [aws_security_group.ecs.id]
      assign_public_ip   = false
    }
  }
}

# ─────────────────────────────────────────────────────────────
# RDS（prod）
# ─────────────────────────────────────────────────────────────

module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${var.project_name}-prod-db"

  engine         = "postgres"
  engine_version = "15"
  instance_class = var.rds_instance_class
  family         = "postgres15"

  db_name  = var.db_name
  username = var.db_username

  manage_master_user_password = true

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.prod.name

  multi_az = true # prod は Multi-AZ 有効（SLA 99.9%）

  storage_type          = "gp3"
  allocated_storage     = 20
  max_allocated_storage = 500

  skip_final_snapshot = false # prod は削除時にスナップショットを保存
  deletion_protection = true  # 誤削除防止
}
