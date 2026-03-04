"""UserStatsService のユニットテスト（RED phase）。

Repository をモックして Service のビジネスロジックを検証する。
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.user_stats_service import UserStatsService


def _make_mock_repo():
    """UserStatsRepository のモックを生成する。"""
    return AsyncMock()


# ---------------------------------------------------------------------------
# get_user_stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_stats():
    """ユーザー統計（累計覚えた種類数）を取得できる。"""
    repo = _make_mock_repo()
    repo.count_correct_breeds.return_value = 42

    service = UserStatsService(repo)
    result = await service.get_user_stats(uuid.uuid4())

    assert result.total_correct_breeds == 42
    repo.count_correct_breeds.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_stats_zero():
    """正解履歴がない場合は 0 を返す。"""
    repo = _make_mock_repo()
    repo.count_correct_breeds.return_value = 0

    service = UserStatsService(repo)
    result = await service.get_user_stats(uuid.uuid4())

    assert result.total_correct_breeds == 0


# ---------------------------------------------------------------------------
# get_latest_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_latest_session_found():
    """最新セッション結果を取得できる（correct_rate を算出する）。"""
    repo = _make_mock_repo()
    session_result = MagicMock()
    session_result.session_id = uuid.uuid4()
    session_result.source = "quiz"
    session_result.correct_count = 7
    session_result.incorrect_count = 3
    session_result.completed_at = datetime.now(UTC)
    repo.get_latest_session_result.return_value = session_result

    service = UserStatsService(repo)
    result = await service.get_latest_session(uuid.uuid4(), source="quiz")

    assert result is not None
    assert result.correct_count == 7
    assert result.incorrect_count == 3
    assert result.correct_rate == 0.7
    assert result.source == "quiz"


@pytest.mark.asyncio
async def test_get_latest_session_not_found():
    """セッション結果がない場合は None を返す。"""
    repo = _make_mock_repo()
    repo.get_latest_session_result.return_value = None

    service = UserStatsService(repo)
    result = await service.get_latest_session(uuid.uuid4(), source="quiz")

    assert result is None


@pytest.mark.asyncio
async def test_get_latest_session_today_source():
    """source=today で最新セッション結果を取得できる。"""
    repo = _make_mock_repo()
    session_result = MagicMock()
    session_result.session_id = uuid.uuid4()
    session_result.source = "today"
    session_result.correct_count = 1
    session_result.incorrect_count = 0
    session_result.completed_at = datetime.now(UTC)
    repo.get_latest_session_result.return_value = session_result

    service = UserStatsService(repo)
    result = await service.get_latest_session(uuid.uuid4(), source="today")

    assert result is not None
    assert result.source == "today"
    assert result.correct_rate == 1.0
    repo.get_latest_session_result.assert_called_once()
