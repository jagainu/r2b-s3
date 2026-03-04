"""MasterRepository のユニットテスト（RED phase）。"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.master_repository import MasterRepository


def _make_mock_session():
    session = AsyncMock()
    return session


def _make_master_item(name: str):
    item = MagicMock()
    item.id = uuid.uuid4()
    item.name = name
    return item


# ---------------------------------------------------------------------------
# coat_colors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_coat_colors():
    """毛色マスター一覧を返す。"""
    session = _make_mock_session()
    items = [_make_master_item("シルバー"), _make_master_item("白")]

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = items
    session.execute.return_value = result_mock

    repo = MasterRepository(session)
    result = await repo.get_coat_colors()

    assert len(result) == 2


# ---------------------------------------------------------------------------
# coat_patterns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_coat_patterns():
    """模様マスター一覧を返す。"""
    session = _make_mock_session()
    items = [_make_master_item("タビー"), _make_master_item("ソリッド")]

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = items
    session.execute.return_value = result_mock

    repo = MasterRepository(session)
    result = await repo.get_coat_patterns()

    assert len(result) == 2


# ---------------------------------------------------------------------------
# coat_lengths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_coat_lengths():
    """毛の長さマスター一覧を返す。"""
    session = _make_mock_session()
    items = [_make_master_item("短毛"), _make_master_item("長毛")]

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = items
    session.execute.return_value = result_mock

    repo = MasterRepository(session)
    result = await repo.get_coat_lengths()

    assert len(result) == 2
