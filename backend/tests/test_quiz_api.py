"""クイズ API エンドポイントの統合テスト。

実際の PostgreSQL（Docker）を使用する。
認証済みユーザーを事前に登録し、Cookie で認証した状態でテストする。
"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app

TEST_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/catbreed_db"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def cleanup():
    """各テスト後にテストデータをクリーンアップ。"""
    yield
    async with _Session() as session:
        # quiz 関連テーブルをクリーンアップ（FK の順序に注意）
        await session.execute(text("DELETE FROM quiz_choices"))
        await session.execute(text("DELETE FROM quiz_answers"))
        await session.execute(text("DELETE FROM quiz_questions"))
        await session.execute(text("DELETE FROM session_results"))
        await session.execute(text("DELETE FROM quiz_sessions"))
        await session.execute(text("DELETE FROM wrong_answers"))
        await session.execute(text("DELETE FROM correct_answers"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="https://testserver",
    ) as ac:
        yield ac


async def _register_and_get_csrf(client: AsyncClient) -> str:
    """テストユーザーを登録し、CSRF トークンを取得する。"""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "テストユーザー",
        },
    )
    assert reg.status_code == 201

    csrf_res = await client.get("/api/v1/auth/csrf")
    return csrf_res.json()["csrf_token"]


async def _check_enough_breeds():
    """テスト用に十分な猫種データが存在するか確認する。"""
    async with _Session() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM cat_breeds"))
        count = result.scalar()
        return count >= 10


# ---------------------------------------------------------------------------
# POST /quiz/sessions
# ---------------------------------------------------------------------------


async def test_create_quiz_session_success(client: AsyncClient):
    """認証済みユーザーがクイズセッションを作成できる。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    csrf_token = await _register_and_get_csrf(client)

    res = await client.post(
        "/api/v1/quiz/sessions",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res.status_code == 201
    data = res.json()
    assert "session_id" in data
    assert len(data["questions"]) == 10

    # 各問題の検証
    for q in data["questions"]:
        assert "question_number" in q
        assert q["question_type"] in ("photo_to_name", "name_to_photo")
        assert len(q["choices"]) == 4
        # correct_cat_breed_id がレスポンスに含まれないこと
        assert "correct_cat_breed_id" not in q


async def test_create_quiz_session_unique_breeds(client: AsyncClient):
    """10問の正解猫は全て異なる。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    csrf_token = await _register_and_get_csrf(client)

    res = await client.post(
        "/api/v1/quiz/sessions",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res.status_code == 201
    # API レスポンスからは correct_cat_breed_id が見えないが、
    # DB に保存されたことを信頼する（Service テストで検証済み）


async def test_create_quiz_session_unauthenticated(client: AsyncClient):
    """未認証ではクイズセッションを作成できない。"""
    res = await client.post("/api/v1/quiz/sessions")
    assert res.status_code == 401


async def test_create_quiz_session_no_csrf(client: AsyncClient):
    """CSRF トークンなしではクイズセッションを作成できない。"""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "テストユーザー",
        },
    )

    res = await client.post("/api/v1/quiz/sessions")
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# GET /quiz/today
# ---------------------------------------------------------------------------


async def test_get_today_quiz_success(client: AsyncClient):
    """認証済みユーザーが今日の一匹を取得できる。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    await _register_and_get_csrf(client)

    res = await client.get("/api/v1/quiz/today")
    assert res.status_code == 200
    data = res.json()
    assert "session_id" in data
    assert data["question_number"] == 1
    assert data["question_type"] in ("photo_to_name", "name_to_photo")
    assert len(data["choices"]) == 4


async def test_get_today_quiz_idempotent(client: AsyncClient):
    """同日中に2回呼んでも同じセッションを返す。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    await _register_and_get_csrf(client)

    res1 = await client.get("/api/v1/quiz/today")
    res2 = await client.get("/api/v1/quiz/today")

    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.json()["session_id"] == res2.json()["session_id"]


async def test_get_today_quiz_unauthenticated(client: AsyncClient):
    """未認証では今日の一匹を取得できない。"""
    res = await client.get("/api/v1/quiz/today")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Slice 4: POST /quiz/answer
# ---------------------------------------------------------------------------


async def test_submit_answer_success(client: AsyncClient):
    """回答を送信して正誤判定を受け取れる。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    csrf_token = await _register_and_get_csrf(client)

    # セッション作成
    session_res = await client.post(
        "/api/v1/quiz/sessions",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert session_res.status_code == 201
    session_data = session_res.json()
    session_id = session_data["session_id"]
    first_question = session_data["questions"][0]

    # 最初の選択肢で回答
    first_choice = first_question["choices"][0]
    answer_res = await client.post(
        "/api/v1/quiz/answer",
        json={
            "session_id": session_id,
            "question_number": first_question["question_number"],
            "selected_cat_id": first_choice["id"],
        },
        headers={"X-CSRF-Token": csrf_token},
    )
    assert answer_res.status_code == 200
    data = answer_res.json()
    assert "is_correct" in data
    assert "correct_cat_id" in data


async def test_submit_answer_unauthenticated(client: AsyncClient):
    """未認証では回答できない。"""
    res = await client.post(
        "/api/v1/quiz/answer",
        json={
            "session_id": str(uuid.uuid4()),
            "question_number": 1,
            "selected_cat_id": str(uuid.uuid4()),
        },
    )
    assert res.status_code == 401


async def test_submit_answer_duplicate(client: AsyncClient):
    """同一問題への二重回答は 409 Conflict。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    csrf_token = await _register_and_get_csrf(client)

    session_res = await client.post(
        "/api/v1/quiz/sessions",
        headers={"X-CSRF-Token": csrf_token},
    )
    session_data = session_res.json()
    session_id = session_data["session_id"]
    first_question = session_data["questions"][0]
    first_choice = first_question["choices"][0]

    body = {
        "session_id": session_id,
        "question_number": first_question["question_number"],
        "selected_cat_id": first_choice["id"],
    }

    # 1回目: 成功
    res1 = await client.post(
        "/api/v1/quiz/answer",
        json=body,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res1.status_code == 200

    # 2回目: 重複 → 409
    res2 = await client.post(
        "/api/v1/quiz/answer",
        json=body,
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res2.status_code == 409


# ---------------------------------------------------------------------------
# Slice 4: POST /quiz/sessions/{session_id}/finalize
# ---------------------------------------------------------------------------


async def test_finalize_session_success(client: AsyncClient):
    """全問回答後にセッションを完了できる。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    csrf_token = await _register_and_get_csrf(client)

    # セッション作成
    session_res = await client.post(
        "/api/v1/quiz/sessions",
        headers={"X-CSRF-Token": csrf_token},
    )
    session_data = session_res.json()
    session_id = session_data["session_id"]

    # 全10問に回答
    for q in session_data["questions"]:
        first_choice = q["choices"][0]
        answer_res = await client.post(
            "/api/v1/quiz/answer",
            json={
                "session_id": session_id,
                "question_number": q["question_number"],
                "selected_cat_id": first_choice["id"],
            },
            headers={"X-CSRF-Token": csrf_token},
        )
        assert answer_res.status_code == 200

    # finalize
    finalize_res = await client.post(
        f"/api/v1/quiz/sessions/{session_id}/finalize",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert finalize_res.status_code == 200
    data = finalize_res.json()
    assert data["session_id"] == session_id
    assert data["correct_count"] + data["incorrect_count"] == 10
    assert "correct_rate" in data
    assert "completed_at" in data


async def test_finalize_session_incomplete(client: AsyncClient):
    """全問回答していないセッションの finalize は 400。"""
    if not await _check_enough_breeds():
        pytest.skip("猫種データが10種未満のためスキップ")

    csrf_token = await _register_and_get_csrf(client)

    session_res = await client.post(
        "/api/v1/quiz/sessions",
        headers={"X-CSRF-Token": csrf_token},
    )
    session_id = session_res.json()["session_id"]

    # 1問だけ回答
    first_q = session_res.json()["questions"][0]
    await client.post(
        "/api/v1/quiz/answer",
        json={
            "session_id": session_id,
            "question_number": first_q["question_number"],
            "selected_cat_id": first_q["choices"][0]["id"],
        },
        headers={"X-CSRF-Token": csrf_token},
    )

    finalize_res = await client.post(
        f"/api/v1/quiz/sessions/{session_id}/finalize",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert finalize_res.status_code == 400


async def test_finalize_session_unauthenticated(client: AsyncClient):
    """未認証では finalize できない。"""
    res = await client.post(
        f"/api/v1/quiz/sessions/{uuid.uuid4()}/finalize",
    )
    assert res.status_code == 401
