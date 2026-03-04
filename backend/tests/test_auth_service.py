"""AuthService の単体テスト。

Repository をモックしてビジネスロジックのみテストする。
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.auth_service import AuthService, GoogleUserInfo


def _make_mock_user(
    user_id: uuid.UUID | None = None,
    email: str = "test@example.com",
    username: str = "テスト",
    password_hash: str | None = "hashed",
    google_id: str | None = None,
):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = email
    user.username = username
    user.password_hash = password_hash
    user.google_id = google_id
    return user


def _make_repo():
    repo = AsyncMock()
    repo.get_by_email = AsyncMock(return_value=None)
    repo.get_by_google_id = AsyncMock(return_value=None)
    repo.create = AsyncMock()
    repo.update_google_id = AsyncMock()
    return repo


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------


async def test_register_success():
    repo = _make_repo()
    user = _make_mock_user()
    repo.create.return_value = user

    service = AuthService(repo)
    result = await service.register("new@example.com", "password123", "ユーザー")

    assert result == user
    repo.get_by_email.assert_awaited_once_with("new@example.com")
    repo.create.assert_awaited_once()


async def test_register_duplicate_email():
    repo = _make_repo()
    repo.get_by_email.return_value = _make_mock_user()

    service = AuthService(repo)
    with pytest.raises(AuthService.EmailAlreadyExistsError):
        await service.register("existing@example.com", "password123", "ユーザー")


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------


async def test_login_success():
    repo = _make_repo()
    user = _make_mock_user(password_hash="$2b$12$dummy")
    repo.get_by_email.return_value = user

    service = AuthService(repo)
    with patch("app.services.auth_service.verify_password", return_value=True):
        result = await service.login("test@example.com", "password123")

    assert result == user


async def test_login_wrong_password():
    repo = _make_repo()
    user = _make_mock_user(password_hash="$2b$12$dummy")
    repo.get_by_email.return_value = user

    service = AuthService(repo)
    with patch("app.services.auth_service.verify_password", return_value=False):
        with pytest.raises(AuthService.InvalidCredentialsError):
            await service.login("test@example.com", "wrongpassword")


async def test_login_user_not_found():
    repo = _make_repo()
    repo.get_by_email.return_value = None

    service = AuthService(repo)
    with pytest.raises(AuthService.InvalidCredentialsError):
        await service.login("notfound@example.com", "password123")


async def test_login_no_password_hash():
    """Google OAuth のみで登録したユーザー（password_hash=None）のパスワードログイン失敗。"""
    repo = _make_repo()
    user = _make_mock_user(password_hash=None)
    repo.get_by_email.return_value = user

    service = AuthService(repo)
    with pytest.raises(AuthService.InvalidCredentialsError):
        await service.login("google-only@example.com", "password123")


# ---------------------------------------------------------------------------
# google_auth
# ---------------------------------------------------------------------------


async def test_google_auth_existing_user_by_google_id():
    """既存の google_id を持つユーザーでログイン。"""
    repo = _make_repo()
    user = _make_mock_user(google_id="google-123")
    repo.get_by_google_id.return_value = user

    service = AuthService(repo)
    google_info = GoogleUserInfo(
        sub="google-123", email="user@gmail.com", name="Googleユーザー"
    )
    result = await service.google_auth(google_info)

    assert result == user
    repo.create.assert_not_awaited()


async def test_google_auth_existing_email_links_google_id():
    """メールが既存だが google_id が未登録 → google_id をリンク。"""
    repo = _make_repo()
    user = _make_mock_user(google_id=None)
    repo.get_by_google_id.return_value = None
    repo.get_by_email.return_value = user
    repo.update_google_id.return_value = user

    service = AuthService(repo)
    google_info = GoogleUserInfo(
        sub="google-new", email=user.email, name="Googleユーザー"
    )
    result = await service.google_auth(google_info)

    assert result == user
    repo.update_google_id.assert_awaited_once_with(user.id, "google-new")


async def test_google_auth_new_user():
    """新規ユーザー → INSERT。"""
    repo = _make_repo()
    new_user = _make_mock_user(
        email="newgoogle@gmail.com", google_id="google-brand-new"
    )
    repo.get_by_google_id.return_value = None
    repo.get_by_email.return_value = None
    repo.create.return_value = new_user

    service = AuthService(repo)
    google_info = GoogleUserInfo(
        sub="google-brand-new", email="newgoogle@gmail.com", name="新規ユーザー"
    )
    result = await service.google_auth(google_info)

    assert result == new_user
    repo.create.assert_awaited_once_with(
        email="newgoogle@gmail.com",
        username="新規ユーザー",
        google_id="google-brand-new",
    )
