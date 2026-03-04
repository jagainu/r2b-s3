"""QuizRepository のユニットテスト（RED phase）。

AsyncSession をモックして Repository メソッドの呼び出しを検証する。
"""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.quiz_repository import QuizRepository


def _make_mock_session():
    """AsyncSession のモックを生成する。"""
    session = AsyncMock()
    return session


def _make_cat_breed(name: str = "アメリカンショートヘア"):
    """テスト用の CatBreed モックを生成する。"""
    breed = MagicMock()
    breed.id = uuid.uuid4()
    breed.name = name
    photo = MagicMock()
    photo.photo_url = f"/static/cat_images/{name}/1.jpg"
    photo.display_order = 1
    breed.photos = [photo]
    return breed


def _make_wrong_answer(cat_breed_id: uuid.UUID, wrong_count: int = 1):
    """テスト用の WrongAnswer モックを生成する。"""
    wa = MagicMock()
    wa.cat_breed_id = cat_breed_id
    wa.wrong_count = wrong_count
    wa.last_wrong_at = datetime.now(UTC)
    return wa


# ---------------------------------------------------------------------------
# get_wrong_answers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_wrong_answers_returns_list():
    """ユーザーの誤答履歴を取得できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    wa1 = _make_wrong_answer(uuid.uuid4(), wrong_count=3)
    wa2 = _make_wrong_answer(uuid.uuid4(), wrong_count=1)

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [wa1, wa2]
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_wrong_answers(user_id)

    assert len(result) == 2
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_wrong_answers_empty():
    """誤答履歴がない場合は空リストを返す。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_wrong_answers(user_id)

    assert result == []


# ---------------------------------------------------------------------------
# get_all_cat_breeds
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_all_cat_breeds():
    """全猫種を写真付きで取得できる。"""
    session = _make_mock_session()
    breeds = [_make_cat_breed("アメリカンショートヘア"), _make_cat_breed("ペルシャ")]

    result_mock = MagicMock()
    result_mock.unique.return_value.scalars.return_value.all.return_value = breeds
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_all_cat_breeds()

    assert len(result) == 2
    session.execute.assert_called_once()


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session():
    """クイズセッションを作成できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    repo = QuizRepository(session)
    result = await repo.create_session(
        user_id=user_id, source="quiz", total_questions=10
    )

    assert result.user_id == user_id
    assert result.source == "quiz"
    assert result.total_questions == 10
    assert result.status == "active"
    session.add.assert_called_once()
    session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_create_session_today():
    """今日の一匹セッションを作成できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    repo = QuizRepository(session)
    result = await repo.create_session(
        user_id=user_id, source="today", total_questions=1
    )

    assert result.source == "today"
    assert result.total_questions == 1


# ---------------------------------------------------------------------------
# create_question
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_question():
    """問題を作成できる。"""
    session = _make_mock_session()
    session_id = uuid.uuid4()
    correct_cat_breed_id = uuid.uuid4()

    repo = QuizRepository(session)
    result = await repo.create_question(
        session_id=session_id,
        question_number=1,
        question_type="photo_to_name",
        correct_cat_breed_id=correct_cat_breed_id,
    )

    assert result.session_id == session_id
    assert result.question_number == 1
    assert result.question_type == "photo_to_name"
    assert result.correct_cat_breed_id == correct_cat_breed_id
    session.add.assert_called_once()
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# create_choices
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_choices():
    """選択肢を一括作成できる。"""
    session = _make_mock_session()
    question_id = uuid.uuid4()
    choices_data = [
        {"choice_order": 1, "cat_breed_id": uuid.uuid4(), "photo_url": None},
        {"choice_order": 2, "cat_breed_id": uuid.uuid4(), "photo_url": None},
        {"choice_order": 3, "cat_breed_id": uuid.uuid4(), "photo_url": None},
        {"choice_order": 4, "cat_breed_id": uuid.uuid4(), "photo_url": None},
    ]

    repo = QuizRepository(session)
    result = await repo.create_choices(question_id=question_id, choices=choices_data)

    assert len(result) == 4
    assert session.add.call_count == 4
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# get_today_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_today_session_found():
    """今日のセッションが存在する場合に返す。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    existing_session = MagicMock()
    existing_session.id = uuid.uuid4()
    existing_session.source = "today"

    result_mock = MagicMock()
    result_mock.unique.return_value.scalar_one_or_none.return_value = existing_session
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_today_session(user_id)

    assert result is not None
    assert result.source == "today"


@pytest.mark.asyncio
async def test_get_today_session_not_found():
    """今日のセッションがない場合は None を返す。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.unique.return_value.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_today_session(user_id)

    assert result is None


# ---------------------------------------------------------------------------
# Slice 4: get_question
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_question_found():
    """セッションIDと問題番号で問題を取得できる。"""
    session = _make_mock_session()
    session_id = uuid.uuid4()
    question_number = 3

    question_mock = MagicMock()
    question_mock.session_id = session_id
    question_mock.question_number = question_number
    question_mock.correct_cat_breed_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = question_mock
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_question(session_id, question_number)

    assert result is not None
    assert result.session_id == session_id
    assert result.question_number == question_number


@pytest.mark.asyncio
async def test_get_question_not_found():
    """存在しない問題は None を返す。"""
    session = _make_mock_session()

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_question(uuid.uuid4(), 99)

    assert result is None


# ---------------------------------------------------------------------------
# Slice 4: create_answer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_answer():
    """回答を作成できる。"""
    session = _make_mock_session()
    session_id = uuid.uuid4()

    repo = QuizRepository(session)
    result = await repo.create_answer(
        session_id=session_id,
        question_number=1,
        selected_cat_breed_id=uuid.uuid4(),
        is_correct=True,
    )

    assert result.session_id == session_id
    assert result.question_number == 1
    assert result.is_correct is True
    session.add.assert_called_once()
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Slice 4: upsert_wrong_answer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_wrong_answer_new():
    """新規の誤答履歴を作成できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()
    cat_breed_id = uuid.uuid4()

    # 既存レコードなし
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    await repo.upsert_wrong_answer(user_id=user_id, cat_breed_id=cat_breed_id)

    session.add.assert_called_once()
    session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_wrong_answer_existing():
    """既存の誤答履歴を更新（wrong_count をインクリメント）できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()
    cat_breed_id = uuid.uuid4()

    existing = MagicMock()
    existing.wrong_count = 2

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = existing
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    await repo.upsert_wrong_answer(user_id=user_id, cat_breed_id=cat_breed_id)

    assert existing.wrong_count == 3
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Slice 4: insert_correct_answer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_insert_correct_answer():
    """正解履歴を作成できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()
    cat_breed_id = uuid.uuid4()

    repo = QuizRepository(session)
    await repo.insert_correct_answer(user_id=user_id, cat_breed_id=cat_breed_id)

    session.execute.assert_called_once()
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Slice 4: count_answers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_count_answers():
    """セッションの回答数と正解数を集計できる。"""
    session = _make_mock_session()
    session_id = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.one.return_value = (10, 7)
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    total, correct = await repo.count_answers(session_id)

    assert total == 10
    assert correct == 7


# ---------------------------------------------------------------------------
# Slice 4: get_session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session():
    """セッションを取得できる。"""
    session = _make_mock_session()
    session_id = uuid.uuid4()

    session_mock = MagicMock()
    session_mock.id = session_id
    session_mock.status = "active"

    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = session_mock
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_session(session_id)

    assert result is not None
    assert result.id == session_id


# ---------------------------------------------------------------------------
# Slice 4: update_session_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_session_status():
    """セッションのステータスを更新できる。"""
    session = _make_mock_session()
    session_obj = MagicMock()
    session_obj.status = "active"

    repo = QuizRepository(session)
    await repo.update_session_status(session_obj, "completed")

    assert session_obj.status == "completed"
    assert session_obj.completed_at is not None
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Slice 4: create_session_result
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session_result():
    """セッション結果を作成できる。"""
    session = _make_mock_session()
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    repo = QuizRepository(session)
    result = await repo.create_session_result(
        user_id=user_id,
        session_id=session_id,
        source="quiz",
        correct_count=7,
        incorrect_count=3,
    )

    assert result.user_id == user_id
    assert result.session_id == session_id
    assert result.correct_count == 7
    assert result.incorrect_count == 3
    session.add.assert_called_once()
    session.flush.assert_called_once()


# ---------------------------------------------------------------------------
# Slice 4: get_choice_cat_ids
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_choice_cat_ids():
    """問題の選択肢に含まれる猫IDリストを取得できる。"""
    session = _make_mock_session()
    question_id = uuid.uuid4()

    cat_id1 = uuid.uuid4()
    cat_id2 = uuid.uuid4()

    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [cat_id1, cat_id2]
    session.execute.return_value = result_mock

    repo = QuizRepository(session)
    result = await repo.get_choice_cat_ids(question_id)

    assert len(result) == 2
    assert cat_id1 in result
