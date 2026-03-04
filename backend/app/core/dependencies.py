import uuid
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    CSRF_TOKEN_COOKIE,
    decode_token,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository

# ---------------------------------------------------------------------------
# DB セッション
# ---------------------------------------------------------------------------

DbSession = Annotated[AsyncSession, Depends(get_db)]


# ---------------------------------------------------------------------------
# 認証済みユーザー取得
# ---------------------------------------------------------------------------

async def _get_current_user(
    db: DbSession,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証が必要です",
    )
    if not access_token:
        raise credentials_exc
    try:
        user_id_str = decode_token(access_token, expected_type="access")
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exc

    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if user is None:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(_get_current_user)]


# ---------------------------------------------------------------------------
# CSRF 検証（POST/PUT/PATCH/DELETE で使用）
# ---------------------------------------------------------------------------

async def verify_csrf(
    request: Request,
    x_csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
    csrf_token_cookie: Annotated[str | None, Cookie(alias=CSRF_TOKEN_COOKIE)] = None,
) -> None:
    """二重送信 Cookie 方式: ヘッダー値と Cookie 値が一致するか検証する。"""
    if not x_csrf_token or not csrf_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRFトークンが不正です",
        )
    if x_csrf_token != csrf_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRFトークンが不正です",
        )


CsrfVerified = Annotated[None, Depends(verify_csrf)]
