"""認証エンドポイントの統合テスト。

実際の PostgreSQL（Docker）を使用する。
各テストは独立したメールアドレスを使用し、autouse フィクスチャでクリーンアップする。
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app

TEST_DB_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/catbreed_db"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def cleanup_users():
    """各テスト後に users テーブルをクリーンアップ。"""
    yield
    async with _Session() as session:
        await session.execute(text("DELETE FROM users"))
        await session.commit()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="https://testserver",
    ) as ac:
        yield ac


def uniq_email() -> str:
    """テストごとに一意なメールアドレスを生成する。"""
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

async def test_register_success(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": uniq_email(),
        "password": "password123",
        "username": "テストユーザー",
    })
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert "email" in data
    assert "username" in data
    assert "access_token" in res.cookies
    assert "refresh_token" in res.cookies


async def test_register_duplicate_email(client: AsyncClient):
    email = uniq_email()
    payload = {"email": email, "password": "password123", "username": "ユーザー"}
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 409


async def test_register_short_password(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": uniq_email(),
        "password": "1234567",   # 7文字（8文字未満）
        "username": "ユーザー",
    })
    assert res.status_code == 422


async def test_register_short_username(client: AsyncClient):
    res = await client.post("/api/v1/auth/register", json={
        "email": uniq_email(),
        "password": "password123",
        "username": "a",   # 1文字（2文字未満）
    })
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

async def test_login_success(client: AsyncClient):
    email = uniq_email()
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "username": "ログインユーザー",
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123",
    })
    assert res.status_code == 200
    assert res.json()["email"] == email
    assert "access_token" in res.cookies


async def test_login_wrong_password(client: AsyncClient):
    email = uniq_email()
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "username": "ユーザー",
    })
    res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "wrongpassword",
    })
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# csrf + me + logout
# ---------------------------------------------------------------------------

async def test_csrf_endpoint(client: AsyncClient):
    res = await client.get("/api/v1/auth/csrf")
    assert res.status_code == 200
    assert "csrf_token" in res.json()
    assert "csrf_token" in res.cookies


async def test_me_authenticated(client: AsyncClient):
    email = uniq_email()
    reg = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "username": "私のアカウント",
    })
    assert reg.status_code == 201
    # Cookie はクライアントに自動保持される
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == email


async def test_me_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


async def test_logout(client: AsyncClient):
    email = uniq_email()
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "username": "ログアウト",
    })
    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    res = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res.status_code == 204
