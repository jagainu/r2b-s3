"""
The Cat API から猫種ごとの画像をダウンロードし、cat_photos テーブルを更新するスクリプト

使い方:
    # APIキーなし（レート制限あり）
    uv run python scripts/fetch_cat_images.py

    # APIキーあり（推奨）
    CAT_API_KEY=your_key uv run python scripts/fetch_cat_images.py

APIキーの取得:
    https://thecatapi.com/ で無料登録

処理内容:
    1. 各猫種の画像を The Cat API から取得（各3枚）
    2. backend/data/cat_images/{猫種名}/ にダウンロード
    3. cat_photos テーブルを新しい URL で上書き更新

注意:
    - 本番移行時は S3 にアップロードして URL を差し替えること
    - APIキーなしの場合は1リクエスト/秒でスロットリング
"""

import asyncio
import os
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, select

from app.core.database import AsyncSessionLocal
from app.models.masters import CatBreed, CatPhoto

# ---------------------------------------------------------------------------
# 猫種名 → The Cat API breed_id マッピング
# ---------------------------------------------------------------------------

BREED_ID_MAP: dict[str, str] = {
    "アメリカンショートヘア": "asho",
    "スコティッシュフォールド": "sfol",
    "ノルウェージャンフォレストキャット": "norw",
    "ペルシャ": "pers",
    "ベンガル": "beng",
    "ラグドール": "ragd",
    "シャム": "siam",
    "ロシアンブルー": "rblu",
    "マンチカン": "munc",
    "メインクーン": "mcoo",
    "ブリティッシュショートヘア": "bsho",
    "アビシニアン": "abys",
    "バーミーズ": "bure",
    "ソマリ": "soma",
    "トンキニーズ": "tonk",
}

IMAGES_PER_BREED = 3
DOWNLOAD_DIR = Path(__file__).parent.parent / "data" / "cat_images"
CAT_API_BASE = "https://api.thecatapi.com/v1"


# ---------------------------------------------------------------------------
# The Cat API からURLを取得
# ---------------------------------------------------------------------------

def fetch_image_urls(breed_id: str, api_key: str | None) -> list[str]:
    headers = {}
    if api_key:
        headers["x-api-key"] = api_key

    with httpx.Client(timeout=15) as client:
        resp = client.get(
            f"{CAT_API_BASE}/images/search",
            params={"breed_ids": breed_id, "limit": IMAGES_PER_BREED},
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    return [item["url"] for item in data]


# ---------------------------------------------------------------------------
# 画像をダウンロード
# ---------------------------------------------------------------------------

def download_image(url: str, dest_path: Path) -> bool:
    if dest_path.exists():
        return True  # スキップ（キャッシュ）
    try:
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"    ⚠️  ダウンロード失敗: {url} → {e}")
        return False


# ---------------------------------------------------------------------------
# DB更新
# ---------------------------------------------------------------------------

async def update_cat_photos(breed_name: str, breed_id_db: object, image_paths: list[Path]) -> None:
    async with AsyncSessionLocal() as session:
        # 既存の写真を削除
        await session.execute(delete(CatPhoto).where(CatPhoto.cat_breed_id == breed_id_db))

        # 新しい写真を挿入
        for order, path in enumerate(image_paths, start=1):
            # 開発用: ローカルパスを相対URLとして保存
            # 本番用: S3 URL に差し替える
            photo_url = f"/static/cat_images/{breed_name}/{path.name}"
            session.add(CatPhoto(
                cat_breed_id=breed_id_db,
                photo_url=photo_url,
                display_order=order,
            ))

        await session.commit()


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

async def main() -> None:
    api_key = os.environ.get("CAT_API_KEY")
    if api_key:
        print(f"🔑 APIキーあり（制限なし）")
    else:
        print("⚠️  APIキーなし（レート制限モード: 1req/秒）")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 保存先: {DOWNLOAD_DIR}\n")

    # DBから猫種一覧を取得
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(CatBreed))
        breeds = result.scalars().all()

    breed_map = {b.name: b.id for b in breeds}
    success_count = 0
    fail_count = 0

    for breed_name, api_breed_id in BREED_ID_MAP.items():
        if breed_name not in breed_map:
            print(f"  ⚠️  スキップ（DB未登録）: {breed_name}")
            continue

        print(f"  🐱 {breed_name} ({api_breed_id})...")

        # URLを取得
        try:
            urls = fetch_image_urls(api_breed_id, api_key)
        except Exception as e:
            print(f"    ✗ API取得失敗: {e}")
            fail_count += 1
            continue

        if not urls:
            print(f"    ✗ 画像なし")
            fail_count += 1
            continue

        # ダウンロード
        downloaded: list[Path] = []
        for i, url in enumerate(urls):
            ext = url.split(".")[-1].split("?")[0] or "jpg"
            fname = f"{i + 1:02d}.{ext}"
            dest = DOWNLOAD_DIR / breed_name / fname
            if download_image(url, dest):
                downloaded.append(dest)
                print(f"    ✓ {fname}")
            else:
                fail_count += 1

        if downloaded:
            await update_cat_photos(breed_name, breed_map[breed_name], downloaded)
            success_count += len(downloaded)

        # レート制限（APIキーなし）
        if not api_key:
            time.sleep(1)

    print(f"\n✅ 完了！")
    print(f"   成功: {success_count} 枚")
    print(f"   失敗: {fail_count} 件")
    print(f"\n📌 次のステップ:")
    print(f"   1. FastAPI で /static をマウントすれば即アクセス可能")
    print(f"   2. 本番デプロイ時は scripts/upload_to_s3.py で S3 に移行")


if __name__ == "__main__":
    asyncio.run(main())
