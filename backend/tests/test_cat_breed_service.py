"""CatBreedService のユニットテスト（RED phase）。

Repository をモックして Service のビジネスロジックを検証する。
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.cat_breed_service import CatBreedService


class _FakeCoatAttr:
    def __init__(self, attr_name: str):
        self.id = uuid.uuid4()
        self.name = attr_name


class _FakePhoto:
    def __init__(self, url: str, order: int = 1):
        self.id = uuid.uuid4()
        self.photo_url = url
        self.display_order = order


class _FakeCatBreed:
    def __init__(self, breed_name: str):
        self.id = uuid.uuid4()
        self.name = breed_name
        self.coat_color = _FakeCoatAttr("シルバー")
        self.coat_pattern = _FakeCoatAttr("タビー")
        self.coat_length = _FakeCoatAttr("短毛")
        self.photos = [_FakePhoto(f"/static/cat_images/{breed_name}/1.jpg")]


class _FakeSimilarCat:
    def __init__(self, breed_name: str):
        self.similar_cat_breed = _FakeCatBreed(breed_name)


def _make_cat_breed(name: str = "アメリカンショートヘア"):
    return _FakeCatBreed(name)


def _make_similar_cat(name: str):
    return _FakeSimilarCat(name)


# ---------------------------------------------------------------------------
# get_breeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_breeds_no_filter():
    """フィルタなしで全猫種リストを取得し、DTO に変換する。"""
    repo = AsyncMock()
    breeds = [_make_cat_breed("アメリカンショートヘア"), _make_cat_breed("ペルシャ")]
    repo.get_all.return_value = breeds

    service = CatBreedService(repo)
    result = await service.get_breeds()

    assert len(result) == 2
    assert result[0].name == "アメリカンショートヘア"
    assert result[0].coat_color.name == "シルバー"
    repo.get_all.assert_called_once()


@pytest.mark.asyncio
async def test_get_breeds_with_filter():
    """フィルタ条件ありで猫種リストを取得する。"""
    repo = AsyncMock()
    color_id = uuid.uuid4()
    breed = _make_cat_breed("ロシアンブルー")
    repo.get_filtered.return_value = [breed]

    service = CatBreedService(repo)
    result = await service.get_breeds(coat_color_id=color_id)

    assert len(result) == 1
    repo.get_filtered.assert_called_once_with(
        coat_color_id=color_id,
        coat_pattern_id=None,
        coat_length_id=None,
    )


@pytest.mark.asyncio
async def test_get_breeds_thumbnail_url():
    """サムネイルは display_order=1 の写真URL。"""
    repo = AsyncMock()
    breed = _make_cat_breed("ベンガル")
    repo.get_all.return_value = [breed]

    service = CatBreedService(repo)
    result = await service.get_breeds()

    assert result[0].thumbnail_url == "/static/cat_images/ベンガル/1.jpg"


@pytest.mark.asyncio
async def test_get_breeds_no_photos_thumbnail_is_none():
    """写真がない場合、サムネイルは None。"""
    repo = AsyncMock()
    breed = _make_cat_breed("テスト猫")
    breed.photos = []
    repo.get_all.return_value = [breed]

    service = CatBreedService(repo)
    result = await service.get_breeds()

    assert result[0].thumbnail_url is None


# ---------------------------------------------------------------------------
# get_breed_detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_breed_detail_found():
    """IDで猫種詳細を取得できる。"""
    repo = AsyncMock()
    breed = _make_cat_breed("メインクーン")
    repo.get_by_id.return_value = breed

    service = CatBreedService(repo)
    result = await service.get_breed_detail(breed.id)

    assert result is not None
    assert result.name == "メインクーン"
    assert len(result.photos) == 1


@pytest.mark.asyncio
async def test_get_breed_detail_not_found():
    """存在しないIDでは None を返す。"""
    repo = AsyncMock()
    repo.get_by_id.return_value = None

    service = CatBreedService(repo)
    result = await service.get_breed_detail(uuid.uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_breed_detail_photos_sorted_by_display_order():
    """写真は display_order 昇順で返す。"""
    repo = AsyncMock()
    breed = _make_cat_breed("ソマリ")

    photo1 = _FakePhoto("/img/2.jpg", order=2)
    photo2 = _FakePhoto("/img/1.jpg", order=1)
    breed.photos = [photo1, photo2]
    repo.get_by_id.return_value = breed

    service = CatBreedService(repo)
    result = await service.get_breed_detail(breed.id)

    assert result.photos[0].display_order == 1
    assert result.photos[1].display_order == 2


# ---------------------------------------------------------------------------
# get_similar_breeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_similar_breeds():
    """類似猫リストを取得できる。"""
    repo = AsyncMock()
    breed_id = uuid.uuid4()
    similar_cats = [
        _make_similar_cat("ブリティッシュショートヘア"),
        _make_similar_cat("スコティッシュフォールド"),
    ]
    repo.get_similar.return_value = similar_cats

    service = CatBreedService(repo)
    result = await service.get_similar_breeds(breed_id)

    assert len(result) == 2
    assert result[0].name == "ブリティッシュショートヘア"
    assert result[0].thumbnail_url is not None


@pytest.mark.asyncio
async def test_get_similar_breeds_empty():
    """類似猫が無い場合は空リストを返す。"""
    repo = AsyncMock()
    repo.get_similar.return_value = []

    service = CatBreedService(repo)
    result = await service.get_similar_breeds(uuid.uuid4())

    assert result == []
