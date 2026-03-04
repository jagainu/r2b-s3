import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.masters import CatBreed, SimilarCat


class CatBreedRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(self) -> list[CatBreed]:
        """全猫種を関連データ込みで取得する。"""
        stmt = (
            select(CatBreed)
            .options(
                joinedload(CatBreed.coat_color),
                joinedload(CatBreed.coat_pattern),
                joinedload(CatBreed.coat_length),
                joinedload(CatBreed.photos),
            )
            .order_by(CatBreed.name)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_filtered(
        self,
        *,
        coat_color_id: uuid.UUID | None = None,
        coat_pattern_id: uuid.UUID | None = None,
        coat_length_id: uuid.UUID | None = None,
    ) -> list[CatBreed]:
        """条件付きで猫種を取得する（AND フィルタ）。"""
        stmt = select(CatBreed).options(
            joinedload(CatBreed.coat_color),
            joinedload(CatBreed.coat_pattern),
            joinedload(CatBreed.coat_length),
            joinedload(CatBreed.photos),
        )

        if coat_color_id is not None:
            stmt = stmt.where(CatBreed.coat_color_id == coat_color_id)
        if coat_pattern_id is not None:
            stmt = stmt.where(CatBreed.coat_pattern_id == coat_pattern_id)
        if coat_length_id is not None:
            stmt = stmt.where(CatBreed.coat_length_id == coat_length_id)

        stmt = stmt.order_by(CatBreed.name)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, breed_id: uuid.UUID) -> CatBreed | None:
        """IDで猫種を取得する（写真・属性込み）。"""
        stmt = (
            select(CatBreed)
            .options(
                joinedload(CatBreed.coat_color),
                joinedload(CatBreed.coat_pattern),
                joinedload(CatBreed.coat_length),
                joinedload(CatBreed.photos),
            )
            .where(CatBreed.id == breed_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_similar(
        self, breed_id: uuid.UUID, *, limit: int = 3
    ) -> list[SimilarCat]:
        """類似猫を優先度順で取得する（最大 limit 件）。"""
        stmt = (
            select(SimilarCat)
            .options(
                joinedload(SimilarCat.similar_cat_breed).joinedload(CatBreed.photos),
            )
            .where(SimilarCat.cat_breed_id == breed_id)
            .order_by(SimilarCat.priority.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
