"""認証エンドポイントの統合テスト。

実際の PostgreSQL（Docker）を使用する。
各テストは独立したメールアドレスを使用し、autouse フィクスチャでクリーンアップする。
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.main import app
from app.services.auth_service import GoogleUserInfo

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
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": uniq_email(),
            "password": "password123",
            "username": "テストユーザー",
        },
    )
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
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": uniq_email(),
            "password": "1234567",  # 7文字（8文字未満）
            "username": "ユーザー",
        },
    )
    assert res.status_code == 422


async def test_register_short_username(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": uniq_email(),
            "password": "password123",
            "username": "a",  # 1文字（2文字未満）
        },
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


async def test_login_success(client: AsyncClient):
    email = uniq_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "ログインユーザー",
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )
    assert res.status_code == 200
    assert res.json()["email"] == email
    assert "access_token" in res.cookies


async def test_login_wrong_password(client: AsyncClient):
    email = uniq_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "ユーザー",
        },
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "wrongpassword",
        },
    )
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
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "私のアカウント",
        },
    )
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
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "ログアウト",
        },
    )
    csrf_res = await client.get("/api/v1/auth/csrf")
    csrf_token = csrf_res.json()["csrf_token"]

    res = await client.post(
        "/api/v1/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert res.status_code == 204


# ---------------------------------------------------------------------------
# refresh
# ---------------------------------------------------------------------------


async def test_refresh_success(client: AsyncClient):
    email = uniq_email()
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "username": "リフレッシュ",
        },
    )
    # refresh_token Cookie を持っている状態で refresh
    res = await client.post("/api/v1/auth/refresh")
    assert res.status_code == 200


async def test_refresh_no_token(client: AsyncClient):
    # Cookie なしで refresh → 401
    res = await client.post("/api/v1/auth/refresh")
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# google auth
# ---------------------------------------------------------------------------


def _mock_google_settings():
    """Google OAuth テスト用: settings の GOOGLE_CLIENT_ID/SECRET をモック。"""
    return patch.object(
        type(settings),
        "GOOGLE_CLIENT_ID",
        new_callable=lambda: property(lambda self: "fake-client-id"),
    ), patch.object(
        type(settings),
        "GOOGLE_CLIENT_SECRET",
        new_callable=lambda: property(lambda self: "fake-client-secret"),
    )


async def test_google_auth_new_user(client: AsyncClient):
    """Google OAuth で新規ユーザー登録。"""
    google_info = GoogleUserInfo(
        sub="google-new-user",
        email="newgoogle@gmail.com",
        name="Google新規",
    )
    with (
        patch(
            "app.api.v1.endpoints.auth.exchange_google_code",
            new_callable=AsyncMock,
            return_value=google_info,
        ),
        patch(
            "app.api.v1.endpoints.auth.settings.GOOGLE_CLIENT_ID",
            "fake-client-id",
        ),
        patch(
            "app.api.v1.endpoints.auth.settings.GOOGLE_CLIENT_SECRET",
            "fake-client-secret",
        ),
    ):
        res = await client.post(
            "/api/v1/auth/google",
            json={
                "code": "fake-auth-code",
                "redirect_uri": "http://localhost:3000/auth/callback",
            },
        )
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "newgoogle@gmail.com"
    assert data["username"] == "Google新規"
    assert "access_token" in res.cookies


async def test_google_auth_existing_user(client: AsyncClient):
    """既存 Google ユーザーでログイン。"""
    google_info = GoogleUserInfo(
        sub="google-existing",
        email="existing@gmail.com",
        name="既存Google",
    )
    # 1回目: 新規登録
    with (
        patch(
            "app.api.v1.endpoints.auth.exchange_google_code",
            new_callable=AsyncMock,
            return_value=google_info,
        ),
        patch(
            "app.api.v1.endpoints.auth.settings.GOOGLE_CLIENT_ID",
            "fake-client-id",
        ),
        patch(
            "app.api.v1.endpoints.auth.settings.GOOGLE_CLIENT_SECRET",
            "fake-client-secret",
        ),
    ):
        r1 = await client.post(
            "/api/v1/auth/google",
            json={
                "code": "fake-code-1",
                "redirect_uri": "http://localhost:3000/auth/callback",
            },
        )
    assert r1.status_code == 200

    # 2回目: 既存ユーザーでログイン
    with (
        patch(
            "app.api.v1.endpoints.auth.exchange_google_code",
            new_callable=AsyncMock,
            return_value=google_info,
        ),
        patch(
            "app.api.v1.endpoints.auth.settings.GOOGLE_CLIENT_ID",
            "fake-client-id",
        ),
        patch(
            "app.api.v1.endpoints.auth.settings.GOOGLE_CLIENT_SECRET",
            "fake-client-secret",
        ),
    ):
        r2 = await client.post(
            "/api/v1/auth/google",
            json={
                "code": "fake-code-2",
                "redirect_uri": "http://localhost:3000/auth/callback",
            },
        )
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


async def test_google_auth_missing_config(client: AsyncClient):
    """GOOGLE_CLIENT_ID が未設定の場合 503 を返す。"""
    with patch("app.api.v1.endpoints.auth.settings") as mock_settings:
        mock_settings.GOOGLE_CLIENT_ID = ""
        mock_settings.GOOGLE_CLIENT_SECRET = "secret"
        res = await client.post(
            "/api/v1/auth/google",
            json={
                "code": "some-code",
                "redirect_uri": "http://localhost:3000/auth/callback",
            },
        )
    assert res.status_code == 503
