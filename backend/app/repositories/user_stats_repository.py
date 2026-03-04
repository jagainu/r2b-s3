"""ユーザー統計関連の Repository 層。

correct_answers の集計と session_results の最新取得を担当する。
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import CorrectAnswer, SessionResult


class UserStatsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def count_correct_breeds(self, user_id: uuid.UUID) -> int:
        """ユーザーが正解したユニーク猫種数を取得する。

        correct_answers は UNIQUE(user_id, cat_breed_id) 制約があるため
        COUNT(*) がそのままユニーク猫種数になる。
        """
        stmt = select(func.count(CorrectAnswer.id)).where(
            CorrectAnswer.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_latest_session_result(
        self, user_id: uuid.UUID, *, source: str
    ) -> SessionResult | None:
        """ユーザーの最新セッション結果を取得する。

        source (quiz / today) で絞り込み、completed_at 降順で最新1件を返す。
        """
        stmt = (
            select(SessionResult)
            .where(
                SessionResult.user_id == user_id,
                SessionResult.source == source,
            )
            .order_by(SessionResult.completed_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
