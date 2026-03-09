"""
quiz_choices テーブルの Wikimedia URL を CloudFront URL に修正するスクリプト

使い方:
    CLOUDFRONT_DOMAIN=d2jw7oizf1q0qb.cloudfront.net \
    uv run python scripts/fix_quiz_choices_urls.py
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update

from app.core.database import AsyncSessionLocal
from app.models.masters import CatPhoto
from app.models.quiz import QuizChoice


async def main() -> None:
    cloudfront_domain = os.environ.get("CLOUDFRONT_DOMAIN", "d2jw7oizf1q0qb.cloudfront.net")
    cloudfront_base = f"https://{cloudfront_domain}"

    async with AsyncSessionLocal() as session:
        # Wikimedia URL を持つ quiz_choices を取得
        result = await session.execute(
            select(QuizChoice).where(
                QuizChoice.photo_url.like("%wikimedia%")
            )
        )
        choices = result.scalars().all()
        print(f"Wikimedia URL in quiz_choices: {len(choices)}")

        if not choices:
            print("修正対象なし。終了します。")
            return

        updated = 0
        for choice in choices:
            # cat_breed_id から cat_photos の最初の写真(display_order=1)を取得
            photo_result = await session.execute(
                select(CatPhoto)
                .where(CatPhoto.cat_breed_id == choice.cat_breed_id)
                .order_by(CatPhoto.display_order)
                .limit(1)
            )
            cat_photo = photo_result.scalar_one_or_none()

            if cat_photo and cat_photo.photo_url and cat_photo.photo_url.startswith(cloudfront_base):
                old_url = choice.photo_url
                choice.photo_url = cat_photo.photo_url
                print(f"  更新: {old_url[:60]}... -> {cat_photo.photo_url}")
                updated += 1
            else:
                print(f"  スキップ (cat_photo なし or CloudFront URL なし): breed_id={choice.cat_breed_id}")

        await session.commit()
        print(f"\n完了: {updated} 件更新")


if __name__ == "__main__":
    asyncio.run(main())
