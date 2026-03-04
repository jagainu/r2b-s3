# Terraform 構成ドキュメント

cloud-diagram.drawio の内容をもとに生成した Terraform スケルトンの設定値まとめ。

## 採用値一覧

| 項目 | 値 | 根拠 |
|------|-----|------|
| `project_name` | `r2b` | リポジトリ名 |
| `aws_region` | `ap-northeast-1` | `backend/.env` の `AWS_REGION` |
| VPC CIDR | `10.0.0.0/16` | stg/prod × public/private の 4 セットが収まる設計 |
| stg ECS CPU / Memory | `256 / 512 MB` | stg は最小スペック |
| prod ECS CPU / Memory | `512 / 1024 MB` | DAU 1,000・ピーク 50 RPS、Auto Scaling なし |
| stg RDS | `db.t3.micro`（Single-AZ） | stg はコスト最小 |
| prod RDS | `db.t3.small`（Multi-AZ） | SLA 99.9% 達成・drawio 仕様に準拠 |
| stg DB 名 | `catbreed_stg` | `backend/.env` の `catbreed_db` から派生 |
| prod DB 名 | `catbreed_prod` | 同上 |
| DB ユーザー名 | `catbreed` | stg/prod 共通 |
| 猫写真 S3 バケット | `r2b-cat-photos` | プロジェクト名ベース（グローバル一意・衝突時は変更） |
| Terraform State S3 | `r2b-terraform-state` | プロジェクト名ベース |
| DynamoDB ロックテーブル | `r2b-terraform-lock` | プロジェクト名ベース |

## ネットワーク設計（サブネット CIDR）

同一 VPC 内に stg / prod をサブネットで分離する構成（drawio 仕様）。

| 用途 | CIDR | 配置サービス |
|------|------|------------|
| stg パブリック AZ-a | `10.0.0.0/24` | ALB（stg） |
| stg パブリック AZ-c | `10.0.1.0/24` | ALB（stg） |
| stg プライベート AZ-a | `10.0.10.0/24` | ECS Fargate（stg）・RDS（stg） |
| stg プライベート AZ-c | `10.0.11.0/24` | ECS Fargate（stg）・RDS（stg） |
| prod パブリック AZ-a | `10.0.100.0/24` | ALB（prod） |
| prod パブリック AZ-c | `10.0.101.0/24` | ALB（prod） |
| prod プライベート AZ-a | `10.0.110.0/24` | ECS Fargate（prod）・RDS（prod） |
| prod プライベート AZ-c | `10.0.111.0/24` | ECS Fargate（prod）・RDS（prod） |

## 生成ファイル構成

```
infrastructure/
├── backend.tf.example            # S3 backend 設定雛形（cp して使う）
├── main.tf                       # 全リソース定義（公式モジュール方式）
├── variables.tf                  # 変数定義（デフォルト値入り）
├── outputs.tf                    # 出力値（ALB DNS・RDS エンドポイント等）
└── environments/
    ├── stg/terraform.tfvars      # stg 用変数値
    └── prod/terraform.tfvars     # prod 用変数値
```

## terraform apply 前の事前作業

```bash
# 1. Terraform State 用 S3 バケットを作成
aws s3 mb s3://r2b-terraform-state --region ap-northeast-1
aws s3api put-bucket-versioning \
  --bucket r2b-terraform-state \
  --versioning-configuration Status=Enabled

# 2. State Lock 用 DynamoDB テーブルを作成
aws dynamodb create-table \
  --table-name r2b-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 3. backend.tf を用意
cp infrastructure/backend.tf.example infrastructure/backend.tf

# 4. 初期化
cd infrastructure
terraform init
```

## 環境別 apply コマンド

```bash
# stg への適用
terraform apply -var-file=environments/stg/terraform.tfvars

# prod への適用
terraform apply -var-file=environments/prod/terraform.tfvars
```

## apply 後にやること

1. **DATABASE_URL を設定する**

   ```bash
   # エンドポイントを確認
   terraform output stg_rds_endpoint
   terraform output prod_rds_endpoint
   ```

   `main.tf` の ECS 環境変数コメントを外して再 apply する：

   ```hcl
   # stg_ecs / prod_ecs の environment ブロック
   { name = "DATABASE_URL", value = "postgresql+asyncpg://catbreed:{password}@{endpoint}/catbreed_stg" }
   ```

   DB パスワードは AWS Secrets Manager に自動保存されている：

   ```bash
   aws secretsmanager list-secrets --query 'SecretList[*].Name'
   ```

2. **CD パイプライン（GitHub Actions）に以下の Secret を設定する**

   | Secret 名 | 内容 |
   |-----------|------|
   | `AWS_ROLE_ARN` | GitHub Actions OIDC 用 IAM ロール ARN |
   | `ECR_REPOSITORY` | `terraform output ecr_repository_url` の値 |
   | `STG_ECS_CLUSTER` | `terraform output stg_ecs_cluster_name` の値 |
   | `STG_ECS_SERVICE` | `terraform output stg_ecs_service_name` の値 |
   | `PROD_ECS_CLUSTER` | `terraform output prod_ecs_cluster_name` の値 |
   | `PROD_ECS_SERVICE` | `terraform output prod_ecs_service_name` の値 |

## 注意事項

- **S3 バケット名はグローバル一意**: `r2b-cat-photos` が衝突する場合は `r2b-cat-photos-{suffix}` に変更する
- **`backend.tf` は Git 管理外**: `.gitignore` に追加済み。各開発者・CI がそれぞれ用意する
- **DB パスワードはコードに書かない**: `manage_master_user_password = true` で AWS が自動生成・Secrets Manager に保存
- **prod RDS の削除保護**: `deletion_protection = true` のため `terraform destroy` 前に手動で無効化が必要
- **image_tag**: CD パイプラインが `TF_VAR_image_tag=<git-sha>` で注入する。手動 apply 時は `latest` がフォールバック
