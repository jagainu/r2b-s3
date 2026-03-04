"""マスターデータ API エンドポイントのテスト（RED phase）。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest


def _sample_master(name: str):
    """マスターデータのモックを返す。"""

    class _Fake:
        pass

    item = _Fake()
    item.id = uuid.uuid4()
    item.name = name
    return item


# ---------------------------------------------------------------------------
# GET /api/v1/masters/coat-colors
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_coat_colors(client):
    """毛色マスター一覧を取得できる。"""
    items = [_sample_master("シルバー"), _sample_master("白")]

    with patch("app.api.v1.endpoints.masters.MasterRepository") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_coat_colors.return_value = items
        MockRepo.return_value = mock_instance

        response = await client.get("/api/v1/masters/coat-colors")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "シルバー"
    assert "id" in data[0]


# ---------------------------------------------------------------------------
# GET /api/v1/masters/coat-patterns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_coat_patterns(client):
    """模様マスター一覧を取得できる。"""
    items = [_sample_master("タビー"), _sample_master("ソリッド")]

    with patch("app.api.v1.endpoints.masters.MasterRepository") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_coat_patterns.return_value = items
        MockRepo.return_value = mock_instance

        response = await client.get("/api/v1/masters/coat-patterns")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /api/v1/masters/coat-lengths
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_coat_lengths(client):
    """毛の長さマスター一覧を取得できる。"""
    items = [_sample_master("短毛"), _sample_master("長毛")]

    with patch("app.api.v1.endpoints.masters.MasterRepository") as MockRepo:
        mock_instance = AsyncMock()
        mock_instance.get_coat_lengths.return_value = items
        MockRepo.return_value = mock_instance

        response = await client.get("/api/v1/masters/coat-lengths")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
