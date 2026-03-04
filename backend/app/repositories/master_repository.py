from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.masters import CoatColor, CoatLength, CoatPattern


class MasterRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_coat_colors(self) -> list[CoatColor]:
        """毛色マスター一覧を返す。"""
        result = await self.db.execute(select(CoatColor).order_by(CoatColor.name))
        return list(result.scalars().all())

    async def get_coat_patterns(self) -> list[CoatPattern]:
        """模様マスター一覧を返す。"""
        result = await self.db.execute(select(CoatPattern).order_by(CoatPattern.name))
        return list(result.scalars().all())

    async def get_coat_lengths(self) -> list[CoatLength]:
        """毛の長さマスター一覧を返す。"""
        result = await self.db.execute(select(CoatLength).order_by(CoatLength.name))
        return list(result.scalars().all())
