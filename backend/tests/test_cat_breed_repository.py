"""CatBreedRepository のユニットテスト（RED phase）。

AsyncSession をモックして Repository メソッドの呼び出しを検証する。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.cat_breed_repository import CatBreedRepository


def _make_mock_session():
    """AsyncSession のモックを生成する。"""
    session = AsyncMock()
    return session


def _make_cat_breed(
    *,
    name: str = "アメリカンショートヘア",
    coat_color_name: str = "シルバー",
    coat_pattern_name: str = "タビー",
    coat_length_name: str = "短毛",
):
    """テスト用の CatBreed モックオブジェクトを生成する。"""
    breed = MagicMock()
    breed.id = uuid.uuid4()
    breed.name = name
    breed.coat_color = MagicMock(id=uuid.uuid4(), name=coat_color_name)
    breed.coat_pattern = MagicMock(id=uuid.uuid4(), name=coat_pattern_name)
    breed.coat_length = MagicMock(id=uuid.uuid4(), name=coat_length_name)

    photo = MagicMock()
    photo.id = uuid.uuid4()
    photo.photo_url = f"/static/cat_images/{name}/1.jpg"
    photo.display_order = 1
    breed.photos = [photo]

    return breed


def _make_similar_cat(*, name: str = "ブリティッシュショートヘア"):
    """テスト用の SimilarCat モックを生成する。"""
    similar = MagicMock()
    similar.similar_cat_breed = MagicMock()
    similar.similar_cat_breed.id = uuid.uuid4()
    similar.similar_cat_breed.name = name

    photo = MagicMock()
    photo.photo_url = f"/static/cat_images/{name}/1.jpg"
    photo.display_order = 1
    similar.similar_cat_breed.photos = [photo]

    return similar


# ---------------------------------------------------------------------------
# get_all / get_filtered
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_all_returns_all_breeds():
    """フィルタなしで全猫種を返す。"""
    session = _make_mock_session()
    breeds = [
        _make_cat_breed(name="アメリカンショートヘア"),
        _make_cat_breed(name="ペルシャ"),
    ]

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = breeds
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_all()

    assert len(result) == 2
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_filtered_by_coat_color():
    """毛色IDでフィルタリングできる。"""
    session = _make_mock_session()
    color_id = uuid.uuid4()
    breed = _make_cat_breed(name="ロシアンブルー")

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [breed]
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_filtered(coat_color_id=color_id)

    assert len(result) == 1
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_filtered_by_multiple_conditions():
    """複数条件の AND フィルタリングができる。"""
    session = _make_mock_session()
    color_id = uuid.uuid4()
    pattern_id = uuid.uuid4()
    length_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_filtered(
        coat_color_id=color_id,
        coat_pattern_id=pattern_id,
        coat_length_id=length_id,
    )

    assert result == []


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_id_returns_breed():
    """IDで猫種を取得できる。"""
    session = _make_mock_session()
    breed = _make_cat_breed()
    breed_id = breed.id

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = breed
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_by_id(breed_id)

    assert result is not None
    assert result.id == breed_id


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found():
    """存在しないIDではNoneを返す。"""
    session = _make_mock_session()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_by_id(uuid.uuid4())

    assert result is None


# ---------------------------------------------------------------------------
# get_similar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_similar_returns_similar_cats():
    """類似猫を取得できる。"""
    session = _make_mock_session()
    breed_id = uuid.uuid4()
    similar_cats = [
        _make_similar_cat(name="ブリティッシュショートヘア"),
        _make_similar_cat(name="スコティッシュフォールド"),
    ]

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = similar_cats
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_similar(breed_id)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_similar_returns_max_3():
    """類似猫は最大3件まで返す。"""
    session = _make_mock_session()
    breed_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [
        _make_similar_cat(name=f"猫{i}") for i in range(3)
    ]
    session.execute.return_value = result_mock

    repo = CatBreedRepository(session)
    result = await repo.get_similar(breed_id)

    assert len(result) <= 3
