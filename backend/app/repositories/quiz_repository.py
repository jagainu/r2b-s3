"""クイズ関連の Repository 層。

quiz_sessions, quiz_questions, quiz_choices, quiz_answers,
wrong_answers, correct_answers, session_results の CRUD を担当する。
"""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import and_, case, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.masters import CatBreed
from app.models.quiz import (
    CorrectAnswer,
    QuizAnswer,
    QuizChoice,
    QuizQuestion,
    QuizSession,
    SessionResult,
    WrongAnswer,
)


class QuizRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_wrong_answers(self, user_id: uuid.UUID) -> list[WrongAnswer]:
        """ユーザーの誤答履歴を wrong_count 降順で取得する。"""
        stmt = (
            select(WrongAnswer)
            .where(WrongAnswer.user_id == user_id)
            .order_by(WrongAnswer.wrong_count.desc(), WrongAnswer.last_wrong_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_all_cat_breeds(self) -> list[CatBreed]:
        """全猫種を写真付きで取得する。"""
        stmt = select(CatBreed).options(joinedload(CatBreed.photos))
        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())

    async def create_session(
        self,
        *,
        user_id: uuid.UUID,
        source: str,
        total_questions: int,
    ) -> QuizSession:
        """クイズセッションを作成する。"""
        session = QuizSession(
            user_id=user_id,
            source=source,
            total_questions=total_questions,
            status="active",
            started_at=datetime.now(UTC),
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def create_question(
        self,
        *,
        session_id: uuid.UUID,
        question_number: int,
        question_type: str,
        correct_cat_breed_id: uuid.UUID,
    ) -> QuizQuestion:
        """問題を作成する。"""
        question = QuizQuestion(
            session_id=session_id,
            question_number=question_number,
            question_type=question_type,
            correct_cat_breed_id=correct_cat_breed_id,
        )
        self.db.add(question)
        await self.db.flush()
        return question

    async def create_choices(
        self,
        *,
        question_id: uuid.UUID,
        choices: list[dict],
    ) -> list[QuizChoice]:
        """選択肢を一括作成する。"""
        choice_objects = []
        for choice_data in choices:
            choice = QuizChoice(
                question_id=question_id,
                choice_order=choice_data["choice_order"],
                cat_breed_id=choice_data["cat_breed_id"],
                photo_url=choice_data.get("photo_url"),
            )
            self.db.add(choice)
            choice_objects.append(choice)
        await self.db.flush()
        return choice_objects

    async def get_today_session(self, user_id: uuid.UUID) -> QuizSession | None:
        """今日の today セッションを取得する（存在しなければ None）。"""
        today = date.today()
        stmt = (
            select(QuizSession)
            .options(
                joinedload(QuizSession.questions)
                .joinedload(QuizQuestion.choices)
                .joinedload(QuizChoice.cat_breed),
                joinedload(QuizSession.questions)
                .joinedload(QuizQuestion.correct_cat_breed)
                .joinedload(CatBreed.photos),
            )
            .where(
                and_(
                    QuizSession.user_id == user_id,
                    QuizSession.source == "today",
                    func.date(QuizSession.started_at) == today,
                )
            )
            .order_by(QuizSession.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.unique().scalar_one_or_none()

    # ------------------------------------------------------------------
    # Slice 4: 回答・採点・履歴記録
    # ------------------------------------------------------------------

    async def get_question(
        self, session_id: uuid.UUID, question_number: int
    ) -> QuizQuestion | None:
        """セッションIDと問題番号で問題を取得する。"""
        stmt = select(QuizQuestion).where(
            and_(
                QuizQuestion.session_id == session_id,
                QuizQuestion.question_number == question_number,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session(self, session_id: uuid.UUID) -> QuizSession | None:
        """セッションを取得する。"""
        stmt = select(QuizSession).where(QuizSession.id == session_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_answer(
        self,
        *,
        session_id: uuid.UUID,
        question_number: int,
        selected_cat_breed_id: uuid.UUID,
        is_correct: bool,
    ) -> QuizAnswer:
        """回答を作成する。"""
        answer = QuizAnswer(
            session_id=session_id,
            question_number=question_number,
            selected_cat_breed_id=selected_cat_breed_id,
            is_correct=is_correct,
        )
        self.db.add(answer)
        await self.db.flush()
        return answer

    async def upsert_wrong_answer(
        self, *, user_id: uuid.UUID, cat_breed_id: uuid.UUID
    ) -> None:
        """誤答履歴を UPSERT する（wrong_count += 1, last_wrong_at = NOW）。"""
        stmt = select(WrongAnswer).where(
            and_(
                WrongAnswer.user_id == user_id,
                WrongAnswer.cat_breed_id == cat_breed_id,
            )
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is None:
            wrong_answer = WrongAnswer(
                user_id=user_id,
                cat_breed_id=cat_breed_id,
                wrong_count=1,
                last_wrong_at=datetime.now(UTC),
            )
            self.db.add(wrong_answer)
        else:
            existing.wrong_count += 1
            existing.last_wrong_at = datetime.now(UTC)

        await self.db.flush()

    async def insert_correct_answer(
        self, *, user_id: uuid.UUID, cat_breed_id: uuid.UUID
    ) -> None:
        """正解履歴を INSERT する（ON CONFLICT DO NOTHING）。"""
        stmt = (
            pg_insert(CorrectAnswer)
            .values(
                user_id=user_id,
                cat_breed_id=cat_breed_id,
                first_correct_at=datetime.now(UTC),
            )
            .on_conflict_do_nothing(constraint="uq_correct_answers")
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def count_answers(self, session_id: uuid.UUID) -> tuple[int, int]:
        """セッションの総回答数と正解数を返す。"""
        stmt = select(
            func.count(QuizAnswer.id),
            func.sum(case((QuizAnswer.is_correct.is_(True), 1), else_=0)),
        ).where(QuizAnswer.session_id == session_id)
        result = await self.db.execute(stmt)
        total, correct = result.one()
        return total, correct or 0

    async def update_session_status(self, session: QuizSession, status: str) -> None:
        """セッションのステータスを更新する。"""
        session.status = status
        if status == "completed":
            session.completed_at = datetime.now(UTC)
        await self.db.flush()

    async def create_session_result(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        source: str,
        correct_count: int,
        incorrect_count: int,
    ) -> SessionResult:
        """セッション結果を作成する。"""
        session_result = SessionResult(
            user_id=user_id,
            session_id=session_id,
            source=source,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
        )
        self.db.add(session_result)
        await self.db.flush()
        return session_result

    async def get_choice_cat_ids(self, question_id: uuid.UUID) -> list[uuid.UUID]:
        """問題の選択肢に含まれる猫IDリストを取得する。"""
        stmt = select(QuizChoice.cat_breed_id).where(
            QuizChoice.question_id == question_id
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
