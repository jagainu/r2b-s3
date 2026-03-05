# infrastructure/environments/shared/main.tf
# ─────────────────────────────────────────────────────────────
# 共有リソース（VPC・ECR・S3・CloudFront）
#
# stg / prod 両環境から参照されるインフラ基盤。
# 初回のみ apply する。
#
# 実行方法（このディレクトリから）:
#   cp backend.tf.example backend.tf  # bucket名などを設定
#   terraform init
#   terraform apply
# ─────────────────────────────────────────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "Terraform"
      Layer     = "shared"
    }
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

# ─────────────────────────────────────────────────────────────
# VPC（stg/prod 共用。サブネットで環境分離）
# ─────────────────────────────────────────────────────────────
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-shared"
  cidr = var.vpc_cidr

  azs = slice(data.aws_availability_zones.available.names, 0, 2)

  # stg サブネット（index 0-1）→ prod サブネット（index 2-3）の順
  public_subnets  = concat(var.stg_public_subnets, var.prod_public_subnets)
  private_subnets = concat(var.stg_private_subnets, var.prod_private_subnets)

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  public_subnet_tags  = { Tier = "public" }
  private_subnet_tags = { Tier = "private" }

  tags = {
    Name = "${var.project_name}-shared-vpc"
  }
}

# ─────────────────────────────────────────────────────────────
# ECR（stg/prod 共用。image_tag で環境を区別）
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
    default_ttl = 86400
    max_ttl     = 31536000
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
