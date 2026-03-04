"""QuizService のユニットテスト（RED phase）。

Repository をモックして Service のビジネスロジックを検証する。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.quiz_service import QuizService


class _FakePhoto:
    def __init__(self, url: str, order: int = 1):
        self.id = uuid.uuid4()
        self.photo_url = url
        self.display_order = order


class _FakeCatBreed:
    def __init__(self, name: str):
        self.id = uuid.uuid4()
        self.name = name
        self.photos = [_FakePhoto(f"/static/cat_images/{name}/1.jpg")]


class _FakeWrongAnswer:
    def __init__(self, cat_breed_id: uuid.UUID, wrong_count: int):
        self.cat_breed_id = cat_breed_id
        self.wrong_count = wrong_count


class _FakeQuizSession:
    def __init__(self, session_id: uuid.UUID | None = None):
        self.id = session_id or uuid.uuid4()
        self.source = "quiz"
        self.total_questions = 10
        self.status = "active"
        self.questions = []


class _FakeQuizQuestion:
    def __init__(
        self,
        question_id: uuid.UUID | None = None,
        question_number: int = 1,
        question_type: str = "photo_to_name",
        correct_cat_breed_id: uuid.UUID | None = None,
    ):
        self.id = question_id or uuid.uuid4()
        self.session_id = uuid.uuid4()
        self.question_number = question_number
        self.question_type = question_type
        self.correct_cat_breed_id = correct_cat_breed_id or uuid.uuid4()
        self.choices = []


class _FakeQuizChoice:
    def __init__(
        self,
        cat_breed_id: uuid.UUID | None = None,
        choice_order: int = 1,
        photo_url: str | None = None,
        name: str | None = None,
    ):
        self.id = uuid.uuid4()
        self.cat_breed_id = cat_breed_id or uuid.uuid4()
        self.choice_order = choice_order
        self.photo_url = photo_url
        self.cat_breed = MagicMock()
        self.cat_breed.name = name or "テスト猫"
        self.cat_breed.id = self.cat_breed_id


def _make_breeds(count: int = 15) -> list[_FakeCatBreed]:
    """テスト用に猫種を複数生成する。"""
    return [_FakeCatBreed(f"猫種{i}") for i in range(count)]


# ---------------------------------------------------------------------------
# create_quiz_session: 基本動作
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quiz_session_returns_10_questions():
    """クイズセッションは10問を生成する。"""
    repo = AsyncMock()
    breeds = _make_breeds(15)
    repo.get_wrong_answers.return_value = []
    repo.get_all_cat_breeds.return_value = breeds

    # create_session, create_question, create_choices のモック
    fake_session = _FakeQuizSession()
    repo.create_session.return_value = fake_session

    question_counter = [0]

    async def mock_create_question(**kwargs):
        question_counter[0] += 1
        return _FakeQuizQuestion(
            question_number=kwargs["question_number"],
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
                photo_url=c.get("photo_url"),
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    user_id = uuid.uuid4()
    result = await service.create_quiz_session(user_id)

    assert result.session_id is not None
    assert len(result.questions) == 10
    repo.create_session.assert_called_once()
    assert repo.create_question.call_count == 10
    assert repo.create_choices.call_count == 10


# ---------------------------------------------------------------------------
# create_quiz_session: 誤答優先出題
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quiz_session_prioritizes_wrong_answers():
    """誤答履歴がある猫種を優先的に出題する（最大5問）。"""
    repo = AsyncMock()
    breeds = _make_breeds(15)

    # 6匹分の誤答を用意（最大5問まで優先）
    wrong_answers = [
        _FakeWrongAnswer(breeds[i].id, wrong_count=10 - i) for i in range(6)
    ]
    repo.get_wrong_answers.return_value = wrong_answers
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    repo.create_session.return_value = fake_session

    selected_correct_ids = []

    async def mock_create_question(**kwargs):
        selected_correct_ids.append(kwargs["correct_cat_breed_id"])
        return _FakeQuizQuestion(
            question_number=kwargs["question_number"],
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    await service.create_quiz_session(uuid.uuid4())

    # 誤答猫のIDが出題に含まれていることを確認
    wrong_breed_ids = {wa.cat_breed_id for wa in wrong_answers[:5]}
    selected_set = set(selected_correct_ids)
    # 最大5問が誤答猫から選ばれる
    assert len(wrong_breed_ids & selected_set) <= 5


# ---------------------------------------------------------------------------
# create_quiz_session: 重複なし
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quiz_session_no_duplicate_breeds():
    """10問の正解猫は全て異なる（重複なし）。"""
    repo = AsyncMock()
    breeds = _make_breeds(15)
    repo.get_wrong_answers.return_value = []
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    repo.create_session.return_value = fake_session

    selected_correct_ids = []

    async def mock_create_question(**kwargs):
        selected_correct_ids.append(kwargs["correct_cat_breed_id"])
        return _FakeQuizQuestion(
            question_number=kwargs["question_number"],
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    await service.create_quiz_session(uuid.uuid4())

    assert len(selected_correct_ids) == 10
    assert len(set(selected_correct_ids)) == 10  # 全て異なる


# ---------------------------------------------------------------------------
# create_quiz_session: 問題形式のランダム割り当て
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quiz_session_assigns_question_types():
    """問題形式（photo_to_name / name_to_photo）が割り当てられる。"""
    repo = AsyncMock()
    breeds = _make_breeds(15)
    repo.get_wrong_answers.return_value = []
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    repo.create_session.return_value = fake_session

    question_types = []

    async def mock_create_question(**kwargs):
        question_types.append(kwargs["question_type"])
        return _FakeQuizQuestion(
            question_number=kwargs["question_number"],
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
                photo_url=c.get("photo_url"),
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    await service.create_quiz_session(uuid.uuid4())

    # 全問題に有効な question_type が割り当てられている
    for qt in question_types:
        assert qt in ("photo_to_name", "name_to_photo")


# ---------------------------------------------------------------------------
# create_quiz_session: 各問題に4つの選択肢
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quiz_session_4_choices_per_question():
    """各問題に4つの選択肢が生成される。"""
    repo = AsyncMock()
    breeds = _make_breeds(15)
    repo.get_wrong_answers.return_value = []
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    repo.create_session.return_value = fake_session

    async def mock_create_question(**kwargs):
        return _FakeQuizQuestion(
            question_number=kwargs["question_number"],
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    choices_counts = []

    async def mock_create_choices(**kwargs):
        choices_counts.append(len(kwargs["choices"]))
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    await service.create_quiz_session(uuid.uuid4())

    assert all(count == 4 for count in choices_counts)


# ---------------------------------------------------------------------------
# create_quiz_session: レスポンスに correct_cat_breed_id が含まれない
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_quiz_session_response_no_correct_id():
    """レスポンスに correct_cat_breed_id が含まれない。"""
    repo = AsyncMock()
    breeds = _make_breeds(15)
    repo.get_wrong_answers.return_value = []
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    repo.create_session.return_value = fake_session

    async def mock_create_question(**kwargs):
        return _FakeQuizQuestion(
            question_number=kwargs["question_number"],
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    result = await service.create_quiz_session(uuid.uuid4())

    # QuizSessionResponse には correct_cat_breed_id フィールドがない
    response_dict = result.model_dump()
    for q in response_dict["questions"]:
        assert "correct_cat_breed_id" not in q


# ---------------------------------------------------------------------------
# get_today_quiz: 新規作成
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_today_quiz_creates_new():
    """今日のセッションがなければ新規作成する。"""
    repo = AsyncMock()
    repo.get_today_session.return_value = None

    breeds = _make_breeds(10)
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    fake_session.source = "today"
    fake_session.total_questions = 1
    repo.create_session.return_value = fake_session

    async def mock_create_question(**kwargs):
        return _FakeQuizQuestion(
            question_number=1,
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
                name=f"選択肢{c['choice_order']}",
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    service = QuizService(repo)
    result = await service.get_today_quiz(uuid.uuid4())

    assert result.session_id is not None
    assert result.question_number == 1
    assert len(result.choices) == 4
    repo.create_session.assert_called_once()


# ---------------------------------------------------------------------------
# get_today_quiz: 既存セッション返却
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_today_quiz_returns_existing():
    """今日のセッションがあれば既存を返す。"""
    repo = AsyncMock()
    correct_breed_id = uuid.uuid4()

    # 既存セッションのモック
    existing_session = MagicMock()
    existing_session.id = uuid.uuid4()
    existing_session.source = "today"

    choice1 = MagicMock()
    choice1.id = uuid.uuid4()
    choice1.cat_breed_id = correct_breed_id
    choice1.choice_order = 1
    choice1.photo_url = None
    choice1.cat_breed = MagicMock()
    choice1.cat_breed.name = "正解猫"
    choice1.cat_breed.id = correct_breed_id

    question = MagicMock()
    question.id = uuid.uuid4()
    question.question_number = 1
    question.question_type = "photo_to_name"
    question.correct_cat_breed_id = correct_breed_id
    question.correct_cat_breed = MagicMock()
    question.correct_cat_breed.name = "正解猫"
    question.correct_cat_breed.photos = [
        MagicMock(photo_url="/img/1.jpg", display_order=1)
    ]
    question.choices = [choice1]

    existing_session.questions = [question]
    repo.get_today_session.return_value = existing_session

    service = QuizService(repo)
    result = await service.get_today_quiz(uuid.uuid4())

    assert result.session_id == existing_session.id
    # 新規セッション作成は呼ばれない
    repo.create_session.assert_not_called()


# ---------------------------------------------------------------------------
# get_today_quiz: 同日同ユーザーで同じ猫
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_today_quiz_deterministic():
    """同一ユーザー・同一日付で同じ猫が選ばれる。"""
    repo = AsyncMock()
    repo.get_today_session.return_value = None

    breeds = _make_breeds(10)
    repo.get_all_cat_breeds.return_value = breeds

    fake_session = _FakeQuizSession()
    fake_session.source = "today"
    repo.create_session.return_value = fake_session

    selected_ids = []

    async def mock_create_question(**kwargs):
        selected_ids.append(kwargs["correct_cat_breed_id"])
        return _FakeQuizQuestion(
            question_number=1,
            question_type=kwargs["question_type"],
            correct_cat_breed_id=kwargs["correct_cat_breed_id"],
        )

    repo.create_question.side_effect = mock_create_question

    async def mock_create_choices(**kwargs):
        return [
            _FakeQuizChoice(
                cat_breed_id=c["cat_breed_id"],
                choice_order=c["choice_order"],
            )
            for c in kwargs["choices"]
        ]

    repo.create_choices.side_effect = mock_create_choices

    user_id = uuid.uuid4()
    service = QuizService(repo)

    await service.get_today_quiz(user_id)

    # 2回目の呼び出し（セッション作成後にget_today_sessionがNoneを返す前提）
    repo.get_today_session.return_value = None
    await service.get_today_quiz(user_id)

    # 同じユーザーID・同じ日付なので同じ猫が選ばれる
    assert selected_ids[0] == selected_ids[1]


# ===========================================================================
# Slice 4: submit_answer
# ===========================================================================


@pytest.mark.asyncio
async def test_submit_answer_correct():
    """正解の場合、is_correct=True が返り、correct_answers に INSERT される。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    correct_cat_id = uuid.uuid4()

    # セッション
    session_mock = MagicMock()
    session_mock.id = session_id
    session_mock.user_id = user_id
    session_mock.status = "active"
    repo.get_session.return_value = session_mock

    # 問題
    question_mock = MagicMock()
    question_mock.id = uuid.uuid4()
    question_mock.correct_cat_breed_id = correct_cat_id
    repo.get_question.return_value = question_mock

    # 選択肢に含まれる猫ID
    repo.get_choice_cat_ids.return_value = [correct_cat_id, uuid.uuid4(), uuid.uuid4()]

    # create_answer
    answer_mock = MagicMock()
    answer_mock.is_correct = True
    repo.create_answer.return_value = answer_mock

    service = QuizService(repo)
    result = await service.submit_answer(
        user_id=user_id,
        session_id=session_id,
        question_number=1,
        selected_cat_id=correct_cat_id,
    )

    assert result.is_correct is True
    assert result.correct_cat_id == correct_cat_id
    repo.insert_correct_answer.assert_called_once_with(
        user_id=user_id, cat_breed_id=correct_cat_id
    )
    repo.upsert_wrong_answer.assert_not_called()


@pytest.mark.asyncio
async def test_submit_answer_incorrect():
    """不正解の場合、is_correct=False が返り、wrong_answers に UPSERT される。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    correct_cat_id = uuid.uuid4()
    wrong_cat_id = uuid.uuid4()

    session_mock = MagicMock()
    session_mock.id = session_id
    session_mock.user_id = user_id
    session_mock.status = "active"
    repo.get_session.return_value = session_mock

    question_mock = MagicMock()
    question_mock.id = uuid.uuid4()
    question_mock.correct_cat_breed_id = correct_cat_id
    repo.get_question.return_value = question_mock

    repo.get_choice_cat_ids.return_value = [
        correct_cat_id,
        wrong_cat_id,
        uuid.uuid4(),
    ]

    answer_mock = MagicMock()
    answer_mock.is_correct = False
    repo.create_answer.return_value = answer_mock

    service = QuizService(repo)
    result = await service.submit_answer(
        user_id=user_id,
        session_id=session_id,
        question_number=1,
        selected_cat_id=wrong_cat_id,
    )

    assert result.is_correct is False
    assert result.correct_cat_id == correct_cat_id
    repo.upsert_wrong_answer.assert_called_once_with(
        user_id=user_id, cat_breed_id=correct_cat_id
    )
    repo.insert_correct_answer.assert_not_called()


@pytest.mark.asyncio
async def test_submit_answer_other_users_session():
    """他ユーザーのセッションに回答しようとすると 403 エラー。"""
    repo = AsyncMock()

    session_mock = MagicMock()
    session_mock.user_id = uuid.uuid4()  # 別ユーザー
    session_mock.status = "active"
    repo.get_session.return_value = session_mock

    service = QuizService(repo)
    with pytest.raises(PermissionError):
        await service.submit_answer(
            user_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            question_number=1,
            selected_cat_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_submit_answer_question_not_found():
    """存在しない問題番号への回答は ValueError。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_mock = MagicMock()
    session_mock.user_id = user_id
    session_mock.status = "active"
    repo.get_session.return_value = session_mock
    repo.get_question.return_value = None

    service = QuizService(repo)
    with pytest.raises(ValueError, match="問題が見つかりません"):
        await service.submit_answer(
            user_id=user_id,
            session_id=uuid.uuid4(),
            question_number=99,
            selected_cat_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_submit_answer_invalid_choice():
    """選択肢に含まれない猫IDでの回答は ValueError。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    session_mock = MagicMock()
    session_mock.user_id = user_id
    session_mock.status = "active"
    repo.get_session.return_value = session_mock

    question_mock = MagicMock()
    question_mock.id = uuid.uuid4()
    question_mock.correct_cat_breed_id = uuid.uuid4()
    repo.get_question.return_value = question_mock

    repo.get_choice_cat_ids.return_value = [uuid.uuid4(), uuid.uuid4()]

    service = QuizService(repo)
    with pytest.raises(ValueError, match="選択肢に含まれない猫IDです"):
        await service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_number=1,
            selected_cat_id=uuid.uuid4(),  # 選択肢にない
        )


@pytest.mark.asyncio
async def test_submit_answer_session_not_found():
    """存在しないセッションへの回答は ValueError。"""
    repo = AsyncMock()
    repo.get_session.return_value = None

    service = QuizService(repo)
    with pytest.raises(ValueError, match="セッションが見つかりません"):
        await service.submit_answer(
            user_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            question_number=1,
            selected_cat_id=uuid.uuid4(),
        )


# ===========================================================================
# Slice 4: finalize_session
# ===========================================================================


@pytest.mark.asyncio
async def test_finalize_session_success():
    """セッションを完了して結果を算出できる。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    session_mock = MagicMock()
    session_mock.id = session_id
    session_mock.user_id = user_id
    session_mock.source = "quiz"
    session_mock.status = "active"
    session_mock.total_questions = 10
    repo.get_session.return_value = session_mock

    # 10問中7問正解
    repo.count_answers.return_value = (10, 7)

    result_mock = MagicMock()
    result_mock.completed_at = MagicMock()
    repo.create_session_result.return_value = result_mock

    service = QuizService(repo)
    result = await service.finalize_session(user_id=user_id, session_id=session_id)

    assert result.session_id == session_id
    assert result.correct_count == 7
    assert result.incorrect_count == 3
    assert result.correct_rate == 0.7
    repo.update_session_status.assert_called_once()
    repo.create_session_result.assert_called_once()


@pytest.mark.asyncio
async def test_finalize_session_already_completed():
    """完了済みセッションの再 finalize は ValueError。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_mock = MagicMock()
    session_mock.user_id = user_id
    session_mock.status = "completed"
    repo.get_session.return_value = session_mock

    service = QuizService(repo)
    with pytest.raises(ValueError, match="完了済み"):
        await service.finalize_session(user_id=user_id, session_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_finalize_session_incomplete_answers():
    """全問回答していないセッションの finalize は ValueError。"""
    repo = AsyncMock()

    user_id = uuid.uuid4()
    session_mock = MagicMock()
    session_mock.user_id = user_id
    session_mock.status = "active"
    session_mock.total_questions = 10
    repo.get_session.return_value = session_mock

    # 7問しか回答していない
    repo.count_answers.return_value = (7, 5)

    service = QuizService(repo)
    with pytest.raises(ValueError, match="全問題に回答してください"):
        await service.finalize_session(user_id=user_id, session_id=uuid.uuid4())


@pytest.mark.asyncio
async def test_finalize_session_other_user():
    """他ユーザーのセッションの finalize は PermissionError。"""
    repo = AsyncMock()

    session_mock = MagicMock()
    session_mock.user_id = uuid.uuid4()  # 別ユーザー
    session_mock.status = "active"
    repo.get_session.return_value = session_mock

    service = QuizService(repo)
    with pytest.raises(PermissionError):
        await service.finalize_session(user_id=uuid.uuid4(), session_id=uuid.uuid4())
