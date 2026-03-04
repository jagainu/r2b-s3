"""UserRepository の統合テスト。

実際の PostgreSQL（Docker）を使用する。
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.repositories.user_repository import UserRepository

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
async def db_session():
    async with _Session() as session:
        yield session


def uniq_email() -> str:
    return f"test-{uuid.uuid4().hex[:8]}@example.com"


# ---------------------------------------------------------------------------
# get_by_google_id
# ---------------------------------------------------------------------------


async def test_get_by_google_id_found(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.create(
        email=uniq_email(),
        username="Googleユーザー",
        google_id="google-123",
    )
    await db_session.commit()

    found = await repo.get_by_google_id("google-123")
    assert found is not None
    assert found.id == user.id
    assert found.google_id == "google-123"


async def test_get_by_google_id_not_found(db_session: AsyncSession):
    repo = UserRepository(db_session)
    found = await repo.get_by_google_id("nonexistent-id")
    assert found is None


# ---------------------------------------------------------------------------
# update_google_id
# ---------------------------------------------------------------------------


async def test_update_google_id(db_session: AsyncSession):
    repo = UserRepository(db_session)
    user = await repo.create(
        email=uniq_email(),
        username="リンクユーザー",
        password_hash="hashed",
    )
    await db_session.commit()

    assert user.google_id is None

    updated = await repo.update_google_id(user.id, "google-456")
    await db_session.commit()

    assert updated is not None
    assert updated.google_id == "google-456"


async def test_update_google_id_user_not_found(db_session: AsyncSession):
    repo = UserRepository(db_session)
    result = await repo.update_google_id(uuid.uuid4(), "google-789")
    assert result is None
