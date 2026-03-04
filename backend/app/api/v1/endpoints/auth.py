import uuid
from typing import Annotated

import httpx
from fastapi import APIRouter, Cookie, HTTPException, Response, status
from jose import JWTError
from sqlalchemy.exc import IntegrityError

from app.api.v1.schemas.auth import (
    CsrfResponse,
    GoogleAuthRequest,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.core.config import settings
from app.core.dependencies import CsrfVerified, CurrentUser, DbSession
from app.core.security import (
    CSRF_TOKEN_COOKIE,
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    hash_password,
    set_auth_cookies,
    verify_password,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService, GoogleUserInfo

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(response: Response, user_id: str) -> None:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    set_auth_cookies(response, access_token, refresh_token)


# ---------------------------------------------------------------------------
# Google OAuth ヘルパー
# ---------------------------------------------------------------------------


async def exchange_google_code(code: str, redirect_uri: str) -> GoogleUserInfo:
    """Google の authorization code をトークンに交換し、ユーザー情報を取得する。"""
    async with httpx.AsyncClient() as client:
        # 1. code → access_token
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google 認証に失敗しました",
            )
        token_data = token_res.json()

        # 2. access_token → userinfo
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        if userinfo_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google ユーザー情報の取得に失敗しました",
            )
        userinfo = userinfo_res.json()

    return GoogleUserInfo(
        sub=userinfo["sub"],
        email=userinfo["email"],
        name=userinfo.get("name", userinfo["email"].split("@")[0]),
    )


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    body: RegisterRequest,
    response: Response,
    db: DbSession,
) -> UserResponse:
    repo = UserRepository(db)

    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このメールアドレスは既に登録されています",
        )

    try:
        user = await repo.create(
            email=body.email,
            username=body.username,
            password_hash=hash_password(body.password),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="このメールアドレスは既に登録されています",
        )

    _issue_tokens(response, str(user.id))
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: DbSession,
) -> UserResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    if (
        not user
        or not user.password_hash
        or not verify_password(body.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    _issue_tokens(response, str(user.id))
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /auth/google 🌐
# ---------------------------------------------------------------------------


@router.post("/google", response_model=UserResponse)
async def google_auth(
    body: GoogleAuthRequest,
    response: Response,
    db: DbSession,
) -> UserResponse:
    # 環境変数チェック
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth が設定されていません。GOOGLE_CLIENT_ID と GOOGLE_CLIENT_SECRET を設定してください。",
        )

    google_info = await exchange_google_code(body.code, body.redirect_uri)

    repo = UserRepository(db)
    service = AuthService(repo)
    user = await service.google_auth(google_info)

    _issue_tokens(response, str(user.id))
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /auth/logout  🔒 ✅CSRF
# ---------------------------------------------------------------------------


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    _current_user: CurrentUser,
    _csrf: CsrfVerified,
) -> None:
    clear_auth_cookies(response)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie()] = None,
) -> dict:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="refresh_token が無効です。再ログインしてください",
    )
    if not refresh_token:
        raise credentials_exc
    try:
        user_id_str = decode_token(refresh_token, expected_type="refresh")
    except JWTError:
        raise credentials_exc

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id_str))
    if not user:
        raise credentials_exc

    new_access = create_access_token(str(user.id))
    response.set_cookie(
        key="access_token",
        value=new_access,
        max_age=15 * 60,
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
    )
    return {}


# ---------------------------------------------------------------------------
# GET /auth/csrf
# ---------------------------------------------------------------------------


@router.get("/csrf", response_model=CsrfResponse)
async def get_csrf_token(response: Response) -> CsrfResponse:
    token = generate_csrf_token()
    response.set_cookie(
        key=CSRF_TOKEN_COOKIE,
        value=token,
        max_age=3600,
        path="/",
        httponly=False,  # JS から読み取れる必要がある
        secure=True,
        samesite="none",
    )
    return CsrfResponse(csrf_token=token)


# ---------------------------------------------------------------------------
# GET /auth/me  🔒
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
