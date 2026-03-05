# infrastructure/environments/shared/oidc.tf
# ─────────────────────────────────────────────────────────────
# GitHub Actions OIDC Provider + IAM Roles
#
# GitHub Actions が AWS 操作を行うための OIDC 認証基盤。
# アクセスキー不要でセキュアな CI/CD を実現する。
# ─────────────────────────────────────────────────────────────

# GitHub OIDC Provider（アカウントに 1 つだけ作成）
resource "aws_iam_openid_connect_provider" "github_actions" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # GitHub Actions の OIDC thumbprint（固定値）
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = {
    Name = "github-actions-oidc"
  }
}

# ─────────────────────────────────────────────────────────────
# 共通: ECR push 権限（stg/prod 両 Role にアタッチ）
# ─────────────────────────────────────────────────────────────

resource "aws_iam_policy" "ecr_push" {
  name        = "github-actions-ecr-push"
  description = "GitHub Actions ECR push policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:DescribeImages",
        ]
        Resource = aws_ecr_repository.backend.arn
      },
    ]
  })
}

# ─────────────────────────────────────────────────────────────
# stg 用 IAM Role
# ─────────────────────────────────────────────────────────────

locals {
  github_repo = "makoto/r2b-s3"
}

resource "aws_iam_role" "github_actions_stg" {
  name        = "github-actions-stg"
  description = "GitHub Actions Role for stg ECS deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github_actions.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          # main ブランチへの push のみ許可
          "token.actions.githubusercontent.com:sub" = "repo:${local.github_repo}:ref:refs/heads/main"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "stg_ecr_push" {
  role       = aws_iam_role.github_actions_stg.name
  policy_arn = aws_iam_policy.ecr_push.arn
}

resource "aws_iam_role_policy" "stg_ecs" {
  name = "github-actions-stg-ecs"
  role = aws_iam_role.github_actions_stg.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
          "ecs:RegisterTaskDefinition",
          "ecs:UpdateService",
          "ecs:RunTask",
          "ecs:ListTasks",
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "ecs:cluster" = "arn:aws:ecs:${var.aws_region}:*:cluster/${var.project_name}-stg-cluster"
          }
        }
      },
      {
        # RegisterTaskDefinition はリソース制限なし（ARN が事前不明のため）
        Effect = "Allow"
        Action = ["ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = "*"
        Condition = {
          StringLike = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      },
    ]
  })
}

# ─────────────────────────────────────────────────────────────
# prod 用 IAM Role
# ─────────────────────────────────────────────────────────────

resource "aws_iam_role" "github_actions_prod" {
  name        = "github-actions-prod"
  description = "GitHub Actions Role for prod ECS deploy (tag push only)"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github_actions.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          # v*.*.* タグ push のみ許可
          "token.actions.githubusercontent.com:sub" = "repo:${local.github_repo}:ref:refs/tags/v*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "prod_ecs" {
  name = "github-actions-prod-ecs"
  role = aws_iam_role.github_actions_prod.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:DescribeTasks",
          "ecs:RegisterTaskDefinition",
          "ecs:UpdateService",
          "ecs:RunTask",
          "ecs:ListTasks",
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            # prod クラスターと stg クラスター両方（stg image の参照のため）
            "ecs:cluster" = [
              "arn:aws:ecs:${var.aws_region}:*:cluster/${var.project_name}-prod-cluster",
              "arn:aws:ecs:${var.aws_region}:*:cluster/${var.project_name}-stg-cluster",
            ]
          }
        }
      },
      {
        Effect = "Allow"
        Action = ["ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition"]
        Resource = "*"
      },
      {
        # prod 用 ECR 読み取り（stg でビルド済みイメージを prod でも pull）
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:DescribeImages",
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = "*"
        Condition = {
          StringLike = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      },
    ]
  })
}
