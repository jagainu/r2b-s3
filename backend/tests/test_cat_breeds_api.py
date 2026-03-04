"""猫種 API エンドポイントのテスト（RED phase）。

httpx AsyncClient で API エンドポイントをテストする。
DB アクセスは行わず、Service 層をモックする。
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.schemas.cat_breeds import (
    CatBreedDetailResponse,
    CatBreedListItem,
    CatPhotoResponse,
    CoatAttributeResponse,
    SimilarCatResponse,
)


def _sample_breed_list_item(name: str = "アメリカンショートヘア") -> CatBreedListItem:
    return CatBreedListItem(
        id=uuid.uuid4(),
        name=name,
        coat_color=CoatAttributeResponse(id=uuid.uuid4(), name="シルバー"),
        coat_pattern=CoatAttributeResponse(id=uuid.uuid4(), name="タビー"),
        coat_length=CoatAttributeResponse(id=uuid.uuid4(), name="短毛"),
        thumbnail_url=f"/static/cat_images/{name}/1.jpg",
    )


def _sample_breed_detail(
    name: str = "アメリカンショートヘア",
) -> CatBreedDetailResponse:
    return CatBreedDetailResponse(
        id=uuid.uuid4(),
        name=name,
        coat_color=CoatAttributeResponse(id=uuid.uuid4(), name="シルバー"),
        coat_pattern=CoatAttributeResponse(id=uuid.uuid4(), name="タビー"),
        coat_length=CoatAttributeResponse(id=uuid.uuid4(), name="短毛"),
        photos=[
            CatPhotoResponse(id=uuid.uuid4(), url="/img/1.jpg", display_order=1),
            CatPhotoResponse(id=uuid.uuid4(), url="/img/2.jpg", display_order=2),
        ],
    )


def _sample_similar(name: str = "ブリティッシュショートヘア") -> SimilarCatResponse:
    return SimilarCatResponse(
        id=uuid.uuid4(),
        name=name,
        thumbnail_url=f"/static/cat_images/{name}/1.jpg",
    )


# ---------------------------------------------------------------------------
# GET /api/v1/cat-breeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cat_breeds_list(client):
    """猫種一覧を取得できる。"""
    items = [
        _sample_breed_list_item("アメリカンショートヘア"),
        _sample_breed_list_item("ペルシャ"),
    ]

    with patch("app.api.v1.endpoints.cat_breeds.CatBreedService") as MockService:
        mock_instance = AsyncMock()
        mock_instance.get_breeds.return_value = items
        MockService.return_value = mock_instance

        response = await client.get("/api/v1/cat-breeds")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "アメリカンショートヘア"
    assert "coat_color" in data[0]
    assert "thumbnail_url" in data[0]


@pytest.mark.asyncio
async def test_get_cat_breeds_with_filter(client):
    """フィルタパラメータで猫種を絞り込める。"""
    color_id = uuid.uuid4()
    items = [_sample_breed_list_item("ロシアンブルー")]

    with patch("app.api.v1.endpoints.cat_breeds.CatBreedService") as MockService:
        mock_instance = AsyncMock()
        mock_instance.get_breeds.return_value = items
        MockService.return_value = mock_instance

        response = await client.get(f"/api/v1/cat-breeds?coat_color_id={color_id}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_cat_breeds_empty(client):
    """該当なしの場合は空リストを返す。"""
    with patch("app.api.v1.endpoints.cat_breeds.CatBreedService") as MockService:
        mock_instance = AsyncMock()
        mock_instance.get_breeds.return_value = []
        MockService.return_value = mock_instance

        response = await client.get("/api/v1/cat-breeds")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# GET /api/v1/cat-breeds/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_cat_breed_detail(client):
    """猫種詳細を取得できる。"""
    detail = _sample_breed_detail("メインクーン")

    with patch("app.api.v1.endpoints.cat_breeds.CatBreedService") as MockService:
        mock_instance = AsyncMock()
        mock_instance.get_breed_detail.return_value = detail
        MockService.return_value = mock_instance

        response = await client.get(f"/api/v1/cat-breeds/{detail.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "メインクーン"
    assert len(data["photos"]) == 2
    assert "coat_color" in data


@pytest.mark.asyncio
async def test_get_cat_breed_detail_not_found(client):
    """存在しないIDでは 404 を返す。"""
    with patch("app.api.v1.endpoints.cat_breeds.CatBreedService") as MockService:
        mock_instance = AsyncMock()
        mock_instance.get_breed_detail.return_value = None
        MockService.return_value = mock_instance

        response = await client.get(f"/api/v1/cat-breeds/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Cat breed not found"


# ---------------------------------------------------------------------------
# GET /api/v1/cat-breeds/{id}/similar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_similar_cats(client):
    """類似猫リストを取得できる。"""
    breed_id = uuid.uuid4()
    similar = [
        _sample_similar("ブリティッシュショートヘア"),
        _sample_similar("スコティッシュフォールド"),
    ]

    with patch("app.api.v1.endpoints.cat_breeds.CatBreedService") as MockService:
        mock_instance = AsyncMock()
        mock_instance.get_similar_breeds.return_value = similar
        MockService.return_value = mock_instance

        response = await client.get(f"/api/v1/cat-breeds/{breed_id}/similar")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "ブリティッシュショートヘア"
    assert "thumbnail_url" in data[0]
