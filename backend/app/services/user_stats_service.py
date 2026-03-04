"""ユーザー統計関連の Service 層。

累計覚えた種類数・最新セッション結果の取得ロジックを担当する。
"""

import uuid

from app.api.v1.schemas.users import LatestSessionResponse, UserStatsResponse
from app.repositories.user_stats_repository import UserStatsRepository


class UserStatsService:
    def __init__(self, repo: UserStatsRepository) -> None:
        self.repo = repo

    async def get_user_stats(self, user_id: uuid.UUID) -> UserStatsResponse:
        """ユーザー統計（累計覚えた種類数）を取得する。"""
        count = await self.repo.count_correct_breeds(user_id)
        return UserStatsResponse(total_correct_breeds=count)

    async def get_latest_session(
        self, user_id: uuid.UUID, *, source: str
    ) -> LatestSessionResponse | None:
        """最新セッション結果を取得する。correct_rate を算出して返す。"""
        result = await self.repo.get_latest_session_result(user_id, source=source)
        if result is None:
            return None

        total = result.correct_count + result.incorrect_count
        correct_rate = result.correct_count / total if total > 0 else 0.0

        return LatestSessionResponse(
            session_id=result.session_id,
            source=result.source,
            correct_count=result.correct_count,
            incorrect_count=result.incorrect_count,
            correct_rate=round(correct_rate, 2),
            completed_at=result.completed_at,
        )
