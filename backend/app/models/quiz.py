import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

# ---------------------------------------------------------------------------
# quiz_sessions（クイズセッション）
# ---------------------------------------------------------------------------


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="quiz_sessions")  # noqa: F821
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    answers: Mapped[list["QuizAnswer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    result: Mapped["SessionResult | None"] = relationship(
        back_populates="session", uselist=False
    )

    __table_args__ = (
        CheckConstraint("source IN ('quiz', 'today')", name="ck_quiz_sessions_source"),
        CheckConstraint(
            "status IN ('active', 'completed')", name="ck_quiz_sessions_status"
        ),
        Index("idx_quiz_sessions_user", "user_id", "started_at"),
    )


# ---------------------------------------------------------------------------
# quiz_questions（出題問題・正解保持）
# ---------------------------------------------------------------------------


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    correct_cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )

    session: Mapped["QuizSession"] = relationship(back_populates="questions")
    correct_cat_breed: Mapped["CatBreed"] = relationship()  # noqa: F821
    choices: Mapped[list["QuizChoice"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("session_id", "question_number", name="uq_quiz_questions"),
        CheckConstraint(
            "question_type IN ('photo_to_name', 'name_to_photo')",
            name="ck_quiz_questions_type",
        ),
    )


# ---------------------------------------------------------------------------
# quiz_choices（選択肢）
# ---------------------------------------------------------------------------


class QuizChoice(Base):
    __tablename__ = "quiz_choices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    choice_order: Mapped[int] = mapped_column(Integer, nullable=False)
    cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    question: Mapped["QuizQuestion"] = relationship(back_populates="choices")
    cat_breed: Mapped["CatBreed"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("question_id", "choice_order", name="uq_quiz_choices_order"),
        UniqueConstraint("question_id", "cat_breed_id", name="uq_quiz_choices_breed"),
    )


# ---------------------------------------------------------------------------
# quiz_answers（回答ログ）
# ---------------------------------------------------------------------------


class QuizAnswer(Base):
    __tablename__ = "quiz_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_number: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["QuizSession"] = relationship(back_populates="answers")
    selected_cat_breed: Mapped["CatBreed"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("session_id", "question_number", name="uq_quiz_answers"),
        # quiz_questions への複合 FK（session_id + question_number）
        ForeignKeyConstraint(
            ["session_id", "question_number"],
            ["quiz_questions.session_id", "quiz_questions.question_number"],
            ondelete="CASCADE",
            name="fk_quiz_answers_question",
        ),
    )


# ---------------------------------------------------------------------------
# wrong_answers（誤答履歴）
# ---------------------------------------------------------------------------


class WrongAnswer(Base):
    __tablename__ = "wrong_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_wrong_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="wrong_answers")  # noqa: F821
    cat_breed: Mapped["CatBreed"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("user_id", "cat_breed_id", name="uq_wrong_answers"),
        CheckConstraint("wrong_count >= 1", name="ck_wrong_answers_count"),
        Index(
            "idx_wrong_answers_user",
            "user_id",
            "wrong_count",
            "last_wrong_at",
        ),
    )


# ---------------------------------------------------------------------------
# correct_answers（正解履歴）
# ---------------------------------------------------------------------------


class CorrectAnswer(Base):
    __tablename__ = "correct_answers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    cat_breed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cat_breeds.id"),
        nullable=False,
    )
    first_correct_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="correct_answers")  # noqa: F821
    cat_breed: Mapped["CatBreed"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("user_id", "cat_breed_id", name="uq_correct_answers"),
        Index("idx_correct_answers_user", "user_id"),
    )


# ---------------------------------------------------------------------------
# session_results（セッション結果）
# ---------------------------------------------------------------------------


class SessionResult(Base):
    __tablename__ = "session_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default="gen_random_uuid()",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id"),
        nullable=False,
        unique=True,
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False)
    incorrect_count: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="session_results")  # noqa: F821
    session: Mapped["QuizSession"] = relationship(back_populates="result")

    __table_args__ = (
        UniqueConstraint("session_id", name="uq_session_results"),
        CheckConstraint(
            "source IN ('quiz', 'today')", name="ck_session_results_source"
        ),
        CheckConstraint("correct_count >= 0", name="ck_session_results_correct"),
        CheckConstraint("incorrect_count >= 0", name="ck_session_results_incorrect"),
        Index(
            "idx_session_results_user",
            "user_id",
            "source",
            "completed_at",
        ),
    )
