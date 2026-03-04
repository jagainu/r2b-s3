import uuid

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    google_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    wrong_answers: Mapped[list["WrongAnswer"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    correct_answers: Mapped[list["CorrectAnswer"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    session_results: Mapped[list["SessionResult"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_users_email", "email", unique=True),
        Index(
            "idx_users_google_id",
            "google_id",
            unique=True,
            postgresql_where="google_id IS NOT NULL",
        ),
    )
