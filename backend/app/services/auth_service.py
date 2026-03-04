"""認証ビジネスロジック。

Repository 層に依存し、パスワード検証・Google OAuth ユーザー照合を行う。
"""

from dataclasses import dataclass

from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository


@dataclass
class GoogleUserInfo:
    """Google API から取得するユーザー情報。"""

    sub: str  # Google の一意 ID
    email: str
    name: str


class AuthService:
    """認証に関するビジネスロジックを集約するサービス。"""

    class EmailAlreadyExistsError(Exception):
        pass

    class InvalidCredentialsError(Exception):
        pass

    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    async def register(self, email: str, password: str, username: str):
        """メール＋パスワードで新規登録する。"""
        existing = await self.repo.get_by_email(email)
        if existing:
            raise self.EmailAlreadyExistsError(
                "このメールアドレスは既に登録されています"
            )
        user = await self.repo.create(
            email=email,
            username=username,
            password_hash=hash_password(password),
        )
        return user

    async def login(self, email: str, password: str):
        """メール＋パスワードでログインする。"""
        user = await self.repo.get_by_email(email)
        if (
            not user
            or not user.password_hash
            or not verify_password(password, user.password_hash)
        ):
            raise self.InvalidCredentialsError(
                "メールアドレスまたはパスワードが正しくありません"
            )
        return user

    async def google_auth(self, google_info: GoogleUserInfo):
        """Google OAuth でログイン/登録する。

        1. google_id で既存ユーザーを検索 → 見つかればそのまま返す
        2. email で既存ユーザーを検索 → 見つかれば google_id をリンク
        3. どちらも見つからなければ新規ユーザーを作成
        """
        # 1. google_id で検索
        user = await self.repo.get_by_google_id(google_info.sub)
        if user:
            return user

        # 2. email で検索 → google_id をリンク
        user = await self.repo.get_by_email(google_info.email)
        if user:
            await self.repo.update_google_id(user.id, google_info.sub)
            return user

        # 3. 新規作成
        user = await self.repo.create(
            email=google_info.email,
            username=google_info.name,
            google_id=google_info.sub,
        )
        return user
