"""
ローカルの猫画像を S3 にアップロードし、DB の photo_url を CloudFront URL に更新するスクリプト

使い方:
    uv run python scripts/upload_to_s3.py \
        --bucket r2b-cat-photos \
        --cloudfront-domain xxxxxx.cloudfront.net

環境変数でも指定可能:
    S3_BUCKET=r2b-cat-photos \
    CLOUDFRONT_DOMAIN=xxxxxx.cloudfront.net \
    uv run python scripts/upload_to_s3.py

事前準備:
    - AWS 認証情報が設定済みであること（~/.aws/credentials または環境変数）
    - Terraform で S3 バケット・CloudFront が作成済みであること
    - backend/data/cat_images/ に画像がダウンロード済みであること（fetch_cat_images.py 実行後）

処理内容:
    1. data/cat_images/{猫種名}/*.{jpg,png} を S3 の cat_images/{猫種名}/ にアップロード
    2. cat_photos テーブルの photo_url を CloudFront URL に更新
"""

import argparse
import asyncio
import mimetypes
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.masters import CatBreed, CatPhoto

IMAGES_DIR = Path(__file__).parent.parent / "data" / "cat_images"
S3_PREFIX = "cat_images"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="猫画像を S3 にアップロードして DB を更新する")
    parser.add_argument(
        "--bucket",
        default=os.environ.get("S3_BUCKET", "r2b-cat-photos"),
        help="S3 バケット名（デフォルト: r2b-cat-photos）",
    )
    parser.add_argument(
        "--cloudfront-domain",
        default=os.environ.get("CLOUDFRONT_DOMAIN"),
        help="CloudFront ドメイン名（例: xxxxxx.cloudfront.net）",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1"),
        help="AWS リージョン（デフォルト: ap-northeast-1）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際にアップロード・DB更新はせず、対象ファイルのみ表示する",
    )
    parser.add_argument(
        "--skip-s3",
        action="store_true",
        help="S3 アップロードをスキップして DB 更新のみ実行する（ECS タスク内で使用）",
    )
    return parser.parse_args()


def upload_file(s3_client, local_path: Path, bucket: str, s3_key: str) -> bool:
    content_type, _ = mimetypes.guess_type(str(local_path))
    extra_args = {"ContentType": content_type or "image/jpeg"}
    try:
        s3_client.upload_file(str(local_path), bucket, s3_key, ExtraArgs=extra_args)
        return True
    except ClientError as e:
        print(f"    ERROR: S3 アップロード失敗: {e}")
        return False


async def update_db_url(breed_name: str, old_prefix: str, new_base_url: str, s3_files: list[str] | None = None) -> int:
    """
    指定猫種の photo_url を新しい CloudFront URL に更新する。
    s3_files: S3 上のファイル名リスト（display_order 順に対応）。
              指定した場合は display_order に基づいてファイル名を割り当てる。
    """
    updated = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(CatBreed).where(CatBreed.name == breed_name)
        )
        breed = result.scalar_one_or_none()
        if not breed:
            return 0

        result = await session.execute(
            select(CatPhoto).where(CatPhoto.cat_breed_id == breed.id).order_by(CatPhoto.display_order)
        )
        photos = result.scalars().all()

        for i, photo in enumerate(photos):
            if s3_files and i < len(s3_files):
                filename = s3_files[i]
            else:
                filename = Path(photo.photo_url).name
            new_url = f"{new_base_url}/{filename}"
            photo.photo_url = new_url
            updated += 1

        await session.commit()
    return updated


async def main() -> None:
    args = parse_args()

    if not args.cloudfront_domain:
        print("ERROR: --cloudfront-domain または環境変数 CLOUDFRONT_DOMAIN を指定してください")
        print()
        print("Terraform output から取得する場合:")
        print("  cd infrastructure/environments/shared")
        print("  terraform output cloudfront_domain_name")
        sys.exit(1)

    cloudfront_base = f"https://{args.cloudfront_domain}"
    print(f"S3 バケット   : {args.bucket}")
    print(f"CloudFront URL: {cloudfront_base}")
    if args.skip_s3:
        print("*** --skip-s3 モード（S3 アップロードをスキップ、DB 更新のみ）***")
    elif args.dry_run:
        print(f"画像ディレクトリ: {IMAGES_DIR}")
        print("*** DRY RUN モード（実際の変更はしません）***")
    else:
        print(f"画像ディレクトリ: {IMAGES_DIR}")
    print()

    s3 = None
    if not args.skip_s3:
        if not IMAGES_DIR.exists():
            print(f"ERROR: 画像ディレクトリが見つかりません: {IMAGES_DIR}")
            print("先に fetch_cat_images.py を実行してください")
            sys.exit(1)

        # S3 クライアントの初期化
        if not args.dry_run:
            try:
                s3 = boto3.client("s3", region_name=args.region)
                # バケットの存在確認
                s3.head_bucket(Bucket=args.bucket)
            except NoCredentialsError:
                print("ERROR: AWS 認証情報が設定されていません")
                print("  ~/.aws/credentials または環境変数 AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY を設定してください")
                sys.exit(1)
            except ClientError as e:
                error_code = e.response["Error"]["Code"]
                if error_code == "404":
                    print(f"ERROR: S3 バケット '{args.bucket}' が見つかりません")
                    print("Terraform で shared インフラを apply 済みか確認してください")
                else:
                    print(f"ERROR: S3 接続エラー: {e}")
                sys.exit(1)

    # --skip-s3 の場合は DB に登録済みの猫種一覧から取得
    if args.skip_s3:
        s3_client = boto3.client("s3", region_name=args.region)
        from app.core.database import AsyncSessionLocal as _Session
        async with _Session() as _sess:
            result = await _sess.execute(select(CatBreed))
            breed_names = [b.name for b in result.scalars().all()]
        breed_dirs_iter = [(name, None) for name in sorted(breed_names)]
    else:
        s3_client = None
        breed_dirs_iter = [(d.name, d) for d in sorted(IMAGES_DIR.iterdir()) if d.is_dir()]

    total_uploaded = 0
    total_db_updated = 0

    for breed_name, breed_dir in breed_dirs_iter:
        new_base_url = f"{cloudfront_base}/{S3_PREFIX}/{breed_name}"

        if args.skip_s3:
            # S3 からファイルリストを取得して display_order 順に対応付け
            s3_prefix = f"{S3_PREFIX}/{breed_name}/"
            response = s3_client.list_objects_v2(Bucket=args.bucket, Prefix=s3_prefix)
            s3_files = sorted(
                obj["Key"].removeprefix(s3_prefix)
                for obj in response.get("Contents", [])
                if not obj["Key"].endswith("/")
            )
            n = await update_db_url(breed_name, f"/static/cat_images/{breed_name}", new_base_url, s3_files)
            total_db_updated += n
            print(f"  {breed_name}: DB {n} 件更新 ({len(s3_files)} ファイル)")
            continue

        images = sorted(breed_dir.glob("*.jpg")) + sorted(breed_dir.glob("*.png"))

        if not images:
            print(f"  SKIP: {breed_name}（画像なし）")
            continue

        print(f"  {breed_name} ({len(images)} 枚)...")

        uploaded_count = 0
        for img_path in images:
            s3_key = f"{S3_PREFIX}/{breed_name}/{img_path.name}"

            if args.dry_run:
                print(f"    [DRY] {img_path.name} -> s3://{args.bucket}/{s3_key}")
                uploaded_count += 1
            else:
                if upload_file(s3, img_path, args.bucket, s3_key):
                    print(f"    OK: {img_path.name}")
                    uploaded_count += 1
                else:
                    print(f"    NG: {img_path.name}")

        total_uploaded += uploaded_count

        if args.dry_run:
            print(f"    [DRY] DB photo_url -> {new_base_url}/{{filename}}")
        else:
            n = await update_db_url(breed_name, f"/static/cat_images/{breed_name}", new_base_url)
            total_db_updated += n
            print(f"    DB: {n} 件更新")

    print()
    print("完了!")
    if not args.skip_s3:
        print(f"  アップロード: {total_uploaded} 枚")
    if not args.dry_run:
        print(f"  DB 更新     : {total_db_updated} 件")
    print()
    print("次のステップ:")
    print("  - Vercel/ECS にデプロイ（Dockerfile から data/ のコピーは不要になります）")


if __name__ == "__main__":
    asyncio.run(main())
