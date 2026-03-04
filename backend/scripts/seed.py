"""
マスターデータ投入スクリプト

使い方:
    uv run python scripts/seed.py

投入内容:
    - coat_colors (毛色) x 8
    - coat_patterns (模様) x 7
    - coat_lengths (毛の長さ) x 4
    - cat_breeds (猫種) x 15
    - cat_photos (猫写真) x 15〜30（各猫種 1〜2枚）
    - similar_cats (類似猫) x 複数ペア

注意:
    - 既存データがある場合はスキップ（冪等）
    - photo_url は Wikipedia Commons の公開URL（開発用）
    - 本番移行時は S3 URL に差し替えること
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.masters import CatBreed, CatPhoto, CoatColor, CoatLength, CoatPattern, SimilarCat


# ---------------------------------------------------------------------------
# マスターデータ定義
# ---------------------------------------------------------------------------

COAT_COLORS = [
    "白",
    "黒",
    "グレー",
    "オレンジ",
    "クリーム",
    "ブラウン",
    "シルバー",
    "ゴールデン",
]

COAT_PATTERNS = [
    "無地",
    "タビー（縞）",
    "スポット",
    "ポインテッド",
    "バイカラー",
    "三毛",
    "チンチラ",
]

COAT_LENGTHS = [
    "短毛",
    "中毛",
    "長毛",
    "無毛",
]

# (名前, 毛色, 模様, 毛の長さ, [写真URL, ...])
CAT_BREEDS_DATA: list[tuple[str, str, str, str, list[str]]] = [
    (
        "アメリカンショートヘア",
        "シルバー",
        "タビー（縞）",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/84/American_Shorthair_Silver_Classic_Tabby.jpg/640px-American_Shorthair_Silver_Classic_Tabby.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4a/American_Shorthair_cat.jpg/640px-American_Shorthair_cat.jpg",
        ],
    ),
    (
        "スコティッシュフォールド",
        "グレー",
        "無地",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Scottish_Fold_cat_wikipedia.jpg/640px-Scottish_Fold_cat_wikipedia.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Scottish_fold.jpg/640px-Scottish_fold.jpg",
        ],
    ),
    (
        "ノルウェージャンフォレストキャット",
        "白",
        "バイカラー",
        "長毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8d/Norwegian_Forest_Cat_Jarvis.jpg/640px-Norwegian_Forest_Cat_Jarvis.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/60/Norwegian_forest_cat_-_face.JPG/640px-Norwegian_forest_cat_-_face.JPG",
        ],
    ),
    (
        "ペルシャ",
        "クリーム",
        "無地",
        "長毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/White_Persian_Cat.jpg/640px-White_Persian_Cat.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Smiley_Persian_Cat.jpg/640px-Smiley_Persian_Cat.jpg",
        ],
    ),
    (
        "ベンガル",
        "オレンジ",
        "スポット",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/ba/Paintedcats_Red_Star_standing.jpg/640px-Paintedcats_Red_Star_standing.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Bengal_cat_-_Petscats.jpg/640px-Bengal_cat_-_Petscats.jpg",
        ],
    ),
    (
        "ラグドール",
        "クリーム",
        "ポインテッド",
        "長毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Ragdoll_cat.jpg/640px-Ragdoll_cat.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Ragdoll_from_Gatil_Raggamuffins.jpg/640px-Ragdoll_from_Gatil_Raggamuffins.jpg",
        ],
    ),
    (
        "シャム",
        "クリーム",
        "ポインテッド",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/25/Siam_lilacpoint.jpg/640px-Siam_lilacpoint.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c3/Balinese-Siamese_8_months.jpg/640px-Balinese-Siamese_8_months.jpg",
        ],
    ),
    (
        "ロシアンブルー",
        "グレー",
        "無地",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Russian_Blue_A1.jpg/640px-Russian_Blue_A1.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/Russian_Blue_male.JPG/640px-Russian_Blue_male.JPG",
        ],
    ),
    (
        "マンチカン",
        "オレンジ",
        "タビー（縞）",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/MunchkinCat.jpg/640px-MunchkinCat.jpg",
        ],
    ),
    (
        "メインクーン",
        "ブラウン",
        "タビー（縞）",
        "長毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/Maine_coon_cat_Random.jpg/640px-Maine_coon_cat_Random.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Maine_Coon_2011.jpg/640px-Maine_Coon_2011.jpg",
        ],
    ),
    (
        "ブリティッシュショートヘア",
        "グレー",
        "無地",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9d/Britishblue.jpg/640px-Britishblue.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/29/British_Short_Hair_cat.jpg/640px-British_Short_Hair_cat.jpg",
        ],
    ),
    (
        "アビシニアン",
        "オレンジ",
        "チンチラ",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Gustav_chocolate.jpg/640px-Gustav_chocolate.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9b/Abyssinian_Bronze.jpg/640px-Abyssinian_Bronze.jpg",
        ],
    ),
    (
        "バーミーズ",
        "ブラウン",
        "無地",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/0/04/Sable_Burmese_Adult.JPG/640px-Sable_Burmese_Adult.JPG",
        ],
    ),
    (
        "ソマリ",
        "オレンジ",
        "チンチラ",
        "長毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/24/Somali_cat.jpg/640px-Somali_cat.jpg",
        ],
    ),
    (
        "トンキニーズ",
        "ブラウン",
        "ポインテッド",
        "短毛",
        [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9a/Tonkinese_cat.jpg/640px-Tonkinese_cat.jpg",
        ],
    ),
]

# (猫種名A, 猫種名B, priority)
SIMILAR_CATS_DATA: list[tuple[str, str, int]] = [
    # グレー無地系
    ("ロシアンブルー", "ブリティッシュショートヘア", 2),
    ("ロシアンブルー", "スコティッシュフォールド", 1),
    ("ブリティッシュショートヘア", "スコティッシュフォールド", 2),
    # ポインテッド系
    ("シャム", "ラグドール", 1),
    ("シャム", "トンキニーズ", 2),
    ("ラグドール", "トンキニーズ", 1),
    # 大型長毛系
    ("ノルウェージャンフォレストキャット", "メインクーン", 2),
    ("ノルウェージャンフォレストキャット", "ペルシャ", 1),
    ("メインクーン", "ペルシャ", 1),
    # チンチラ系（ティッキングタビー）
    ("アビシニアン", "ソマリ", 2),
    # オレンジスポット系
    ("ベンガル", "アビシニアン", 1),
]


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

async def get_or_skip(session: AsyncSession, model, name: str) -> object:
    """同名レコードが存在すればそれを返し、なければ新規作成して返す"""
    result = await session.execute(select(model).where(model.name == name))
    obj = result.scalar_one_or_none()
    if obj is None:
        obj = model(name=name)
        session.add(obj)
        await session.flush()
    return obj


# ---------------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------------

async def seed(session: AsyncSession) -> None:
    print("🌱 シードデータ投入を開始します...")

    # ---- 毛色 ----
    print("  毛色 (coat_colors) を投入...")
    color_map: dict[str, CoatColor] = {}
    for name in COAT_COLORS:
        color_map[name] = await get_or_skip(session, CoatColor, name)

    # ---- 模様 ----
    print("  模様 (coat_patterns) を投入...")
    pattern_map: dict[str, CoatPattern] = {}
    for name in COAT_PATTERNS:
        pattern_map[name] = await get_or_skip(session, CoatPattern, name)

    # ---- 毛の長さ ----
    print("  毛の長さ (coat_lengths) を投入...")
    length_map: dict[str, CoatLength] = {}
    for name in COAT_LENGTHS:
        length_map[name] = await get_or_skip(session, CoatLength, name)

    await session.flush()

    # ---- 猫種 + 写真 ----
    print("  猫種 (cat_breeds) と写真 (cat_photos) を投入...")
    breed_map: dict[str, CatBreed] = {}
    for breed_name, color_name, pattern_name, length_name, photo_urls in CAT_BREEDS_DATA:
        # 猫種を get or create
        result = await session.execute(select(CatBreed).where(CatBreed.name == breed_name))
        breed = result.scalar_one_or_none()
        if breed is None:
            breed = CatBreed(
                name=breed_name,
                coat_color_id=color_map[color_name].id,
                coat_pattern_id=pattern_map[pattern_name].id,
                coat_length_id=length_map[length_name].id,
            )
            session.add(breed)
            await session.flush()

            # 写真を投入
            for order, url in enumerate(photo_urls, start=1):
                photo = CatPhoto(
                    cat_breed_id=breed.id,
                    photo_url=url,
                    display_order=order,
                )
                session.add(photo)

        breed_map[breed_name] = breed

    await session.flush()

    # ---- 類似猫 ----
    print("  類似猫 (similar_cats) を投入...")
    for name_a, name_b, priority in SIMILAR_CATS_DATA:
        breed_a = breed_map.get(name_a)
        breed_b = breed_map.get(name_b)
        if breed_a is None or breed_b is None:
            print(f"    ⚠️  スキップ: {name_a} or {name_b} が見つかりません")
            continue

        # 既存チェック（片方向のみ。DBトリガーが逆方向を自動挿入する）
        result = await session.execute(
            select(SimilarCat).where(
                SimilarCat.cat_breed_id == breed_a.id,
                SimilarCat.similar_cat_breed_id == breed_b.id,
            )
        )
        if result.scalar_one_or_none() is None:
            session.add(SimilarCat(
                cat_breed_id=breed_a.id,
                similar_cat_breed_id=breed_b.id,
                priority=priority,
            ))

    await session.commit()
    print("✅ シードデータ投入完了！")
    print(f"   毛色: {len(COAT_COLORS)} 件")
    print(f"   模様: {len(COAT_PATTERNS)} 件")
    print(f"   毛の長さ: {len(COAT_LENGTHS)} 件")
    print(f"   猫種: {len(CAT_BREEDS_DATA)} 件")
    print(f"   類似猫ペア: {len(SIMILAR_CATS_DATA)} 件（DBトリガーで逆方向も自動追加）")


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(main())
