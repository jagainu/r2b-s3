"""ユーザー統計 API エンドポイントの統合テスト。

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
        await session.execute(text("DELETE FROM session_results"))
        await session.execute(text("DELETE FROM quiz_answers"))
        await session.execute(text("DELETE FROM quiz_choices"))
        await session.execute(text("DELETE FROM quiz_questions"))
        await session.execute(text("DELETE FROM quiz_sessions"))
        await session.execute(text("DELETE FROM correct_answers"))
        await session.execute(text("DELETE FROM wrong_answers"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="https://testserver",
    ) as ac:
        yield ac


async def _register_and_login(client: AsyncClient) -> None:
    """テストユーザーを登録する（Cookie がクライアントに保持される）。"""
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "テストユーザー",
        },
    )
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# GET /users/me/stats
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_stats_success(client: AsyncClient):
    """認証済みユーザーが統計を取得できる。"""
    await _register_and_login(client)

    res = await client.get("/api/v1/users/me/stats")
    assert res.status_code == 200

    data = res.json()
    assert "total_correct_breeds" in data
    assert data["total_correct_breeds"] == 0  # 新規ユーザーなので0


@pytest.mark.asyncio
async def test_get_user_stats_unauthenticated(client: AsyncClient):
    """未認証ユーザーは 401 を返す。"""
    res = await client.get("/api/v1/users/me/stats")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# GET /users/me/sessions/latest
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_latest_session_not_found(client: AsyncClient):
    """セッション結果がない場合は 404 を返す。"""
    await _register_and_login(client)

    res = await client.get("/api/v1/users/me/sessions/latest?source=quiz")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_session_unauthenticated(client: AsyncClient):
    """未認証ユーザーは 401 を返す。"""
    res = await client.get("/api/v1/users/me/sessions/latest?source=quiz")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_latest_session_missing_source(client: AsyncClient):
    """source パラメータがない場合は 422 を返す。"""
    await _register_and_login(client)

    res = await client.get("/api/v1/users/me/sessions/latest")
    assert res.status_code == 422
