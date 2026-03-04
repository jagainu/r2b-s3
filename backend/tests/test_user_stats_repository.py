"""UserStatsRepository のユニットテスト（RED phase）。

AsyncSession をモックして Repository メソッドの呼び出しを検証する。
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.user_stats_repository import UserStatsRepository


def _make_mock_session():
    """AsyncSession のモックを生成する。"""
    return AsyncMock()


# ---------------------------------------------------------------------------
# count_correct_breeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_correct_breeds():
    """ユーザーが正解したユニーク猫種数を取得できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one.return_value = 42
    session.execute.return_value = result_mock

    repo = UserStatsRepository(session)
    count = await repo.count_correct_breeds(user_id)

    assert count == 42
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_count_correct_breeds_zero():
    """正解履歴がない場合は 0 を返す。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one.return_value = 0
    session.execute.return_value = result_mock

    repo = UserStatsRepository(session)
    count = await repo.count_correct_breeds(user_id)

    assert count == 0


# ---------------------------------------------------------------------------
# get_latest_session_result
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_latest_session_result_found():
    """最新セッション結果を取得できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    result_obj = MagicMock()
    result_obj.session_id = uuid.uuid4()
    result_obj.source = "quiz"
    result_obj.correct_count = 7
    result_obj.incorrect_count = 3
    result_obj.completed_at = datetime.now(UTC)

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = result_obj
    session.execute.return_value = result_mock

    repo = UserStatsRepository(session)
    result = await repo.get_latest_session_result(user_id, source="quiz")

    assert result is not None
    assert result.source == "quiz"
    assert result.correct_count == 7
    assert result.incorrect_count == 3
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_latest_session_result_not_found():
    """セッション結果がない場合は None を返す。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    repo = UserStatsRepository(session)
    result = await repo.get_latest_session_result(user_id, source="quiz")

    assert result is None
