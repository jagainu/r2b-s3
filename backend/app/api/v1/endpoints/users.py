"""ユーザー統計関連のエンドポイント。

GET /users/me/stats - ユーザー統計（累計覚えた種類数）
GET /users/me/sessions/latest - 最新セッション結果
"""

from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas.users import LatestSessionResponse, UserStatsResponse
from app.core.dependencies import CurrentUser, DbSession
from app.repositories.user_stats_repository import UserStatsRepository
from app.services.user_stats_service import UserStatsService

router = APIRouter(prefix="/users", tags=["users"])


# ---------------------------------------------------------------------------
# GET /users/me/stats  🔒
# ---------------------------------------------------------------------------


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_user_stats(
    db: DbSession,
    current_user: CurrentUser,
) -> UserStatsResponse:
    """ユーザー統計（累計覚えた種類数）を取得する。"""
    repo = UserStatsRepository(db)
    service = UserStatsService(repo)
    return await service.get_user_stats(current_user.id)


# ---------------------------------------------------------------------------
# GET /users/me/sessions/latest  🔒
# ---------------------------------------------------------------------------


@router.get("/me/sessions/latest", response_model=LatestSessionResponse)
async def get_latest_session(
    db: DbSession,
    current_user: CurrentUser,
    source: str = Query(..., description="セッション種別 (quiz / today)"),
) -> LatestSessionResponse:
    """最新セッション結果を取得する。"""
    repo = UserStatsRepository(db)
    service = UserStatsService(repo)
    result = await service.get_latest_session(current_user.id, source=source)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No session found",
        )
    return result
