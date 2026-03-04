"""クイズ関連の Service 層。

セッション生成・問題出題・誤答優先ロジック・今日の一匹を担当する。
"""

import hashlib
import random
import uuid
from datetime import date

from app.api.v1.schemas.quiz import (
    AnswerResponse,
    FinalizeResponse,
    QuizChoiceResponse,
    QuizQuestionResponse,
    QuizSessionResponse,
    TodayQuizResponse,
)
from app.repositories.quiz_repository import QuizRepository


def _get_thumbnail_url(breed) -> str | None:
    """display_order=1 の写真URLを取得する。"""
    if not breed.photos:
        return None
    sorted_photos = sorted(breed.photos, key=lambda p: p.display_order)
    return sorted_photos[0].photo_url


class QuizService:
    def __init__(self, repo: QuizRepository) -> None:
        self.repo = repo

    # ------------------------------------------------------------------
    # POST /quiz/sessions
    # ------------------------------------------------------------------

    async def create_quiz_session(self, user_id: uuid.UUID) -> QuizSessionResponse:
        """クイズセッションを作成し、10問を一括生成する。"""
        total_questions = 10

        # 1. 誤答履歴と全猫種を取得
        wrong_answers = await self.repo.get_wrong_answers(user_id)
        all_breeds = await self.repo.get_all_cat_breeds()

        if len(all_breeds) < total_questions:
            raise ValueError(
                f"猫種が{total_questions}種未満のためクイズを生成できません"
            )

        # 2. 出題猫を選択（誤答優先 + ランダム）
        selected_breeds = self._select_breeds(
            all_breeds=all_breeds,
            wrong_answers=wrong_answers,
            count=total_questions,
        )

        # 3. セッション作成
        session = await self.repo.create_session(
            user_id=user_id,
            source="quiz",
            total_questions=total_questions,
        )

        # 4. 各問題を生成
        questions_response: list[QuizQuestionResponse] = []
        for i, correct_breed in enumerate(selected_breeds, start=1):
            question_type = random.choice(["photo_to_name", "name_to_photo"])

            question = await self.repo.create_question(
                session_id=session.id,
                question_number=i,
                question_type=question_type,
                correct_cat_breed_id=correct_breed.id,
            )

            # 選択肢生成（正解1 + 不正解3）
            choice_breeds = self._select_choice_breeds(
                correct_breed=correct_breed,
                all_breeds=all_breeds,
                count=4,
            )
            random.shuffle(choice_breeds)

            choices_data = []
            for order, cb in enumerate(choice_breeds, start=1):
                photo_url = (
                    _get_thumbnail_url(cb) if question_type == "name_to_photo" else None
                )
                choices_data.append(
                    {
                        "choice_order": order,
                        "cat_breed_id": cb.id,
                        "photo_url": photo_url,
                    }
                )

            created_choices = await self.repo.create_choices(
                question_id=question.id,
                choices=choices_data,
            )

            # レスポンス構築
            choice_responses = self._build_choice_responses(
                created_choices, choice_breeds, question_type
            )

            photo_url = (
                _get_thumbnail_url(correct_breed)
                if question_type == "photo_to_name"
                else None
            )
            cat_name = correct_breed.name if question_type == "name_to_photo" else None

            questions_response.append(
                QuizQuestionResponse(
                    question_number=i,
                    question_type=question_type,
                    photo_url=photo_url,
                    cat_name=cat_name,
                    choices=choice_responses,
                )
            )

        return QuizSessionResponse(
            session_id=session.id,
            questions=questions_response,
        )

    # ------------------------------------------------------------------
    # GET /quiz/today
    # ------------------------------------------------------------------

    async def get_today_quiz(self, user_id: uuid.UUID) -> TodayQuizResponse:
        """今日の一匹クイズを取得する。既存セッションがあればそれを返す。"""
        # 既存セッションチェック
        existing = await self.repo.get_today_session(user_id)
        if existing is not None:
            return self._build_today_response_from_existing(existing)

        # 新規作成
        all_breeds = await self.repo.get_all_cat_breeds()
        if not all_breeds:
            raise ValueError("猫種データがありません")

        # 日付 + ユーザーID で deterministic に猫を選択
        correct_breed = self._select_today_breed(user_id, all_breeds)
        question_type = self._select_today_question_type(user_id)

        session = await self.repo.create_session(
            user_id=user_id,
            source="today",
            total_questions=1,
        )

        question = await self.repo.create_question(
            session_id=session.id,
            question_number=1,
            question_type=question_type,
            correct_cat_breed_id=correct_breed.id,
        )

        # 選択肢
        choice_breeds = self._select_choice_breeds(
            correct_breed=correct_breed,
            all_breeds=all_breeds,
            count=4,
            seed=self._today_seed(user_id),
        )

        choices_data = []
        for order, cb in enumerate(choice_breeds, start=1):
            photo_url = (
                _get_thumbnail_url(cb) if question_type == "name_to_photo" else None
            )
            choices_data.append(
                {
                    "choice_order": order,
                    "cat_breed_id": cb.id,
                    "photo_url": photo_url,
                }
            )

        created_choices = await self.repo.create_choices(
            question_id=question.id,
            choices=choices_data,
        )

        choice_responses = self._build_choice_responses(
            created_choices, choice_breeds, question_type
        )

        photo_url = (
            _get_thumbnail_url(correct_breed)
            if question_type == "photo_to_name"
            else None
        )
        cat_name = correct_breed.name if question_type == "name_to_photo" else None

        return TodayQuizResponse(
            session_id=session.id,
            question_type=question_type,
            question_number=1,
            photo_url=photo_url,
            cat_name=cat_name,
            choices=choice_responses,
        )

    # ------------------------------------------------------------------
    # Private: 猫種選択ロジック
    # ------------------------------------------------------------------

    def _select_breeds(
        self,
        *,
        all_breeds: list,
        wrong_answers: list,
        count: int,
    ) -> list:
        """誤答優先で重複なしに出題猫を選択する。

        最大5問を誤答猫から、残りはランダムに選択する。
        """
        max_priority = min(5, len(wrong_answers))
        breed_map = {b.id: b for b in all_breeds}

        # 誤答猫（wrong_count 降順で最大5匹）
        priority_breeds = []
        for wa in wrong_answers[:max_priority]:
            if wa.cat_breed_id in breed_map:
                priority_breeds.append(breed_map[wa.cat_breed_id])

        selected = list(priority_breeds)
        selected_ids = {b.id for b in selected}

        # 残りをランダムで補充
        remaining = [b for b in all_breeds if b.id not in selected_ids]
        needed = count - len(selected)
        if needed > 0:
            random_picks = random.sample(remaining, min(needed, len(remaining)))
            selected.extend(random_picks)

        return selected[:count]

    def _select_choice_breeds(
        self,
        *,
        correct_breed,
        all_breeds: list,
        count: int = 4,
        seed: int | None = None,
    ) -> list:
        """正解1 + 不正解(count-1)の選択肢猫を選ぶ。"""
        others = [b for b in all_breeds if b.id != correct_breed.id]
        if seed is not None:
            rng = random.Random(seed)
            wrong_choices = rng.sample(others, min(count - 1, len(others)))
        else:
            wrong_choices = random.sample(others, min(count - 1, len(others)))
        result = [correct_breed] + wrong_choices
        if seed is not None:
            rng = random.Random(seed + 1)
            rng.shuffle(result)
        else:
            random.shuffle(result)
        return result

    def _select_today_breed(self, user_id: uuid.UUID, breeds: list):
        """日付 + ユーザーID で deterministic に猫を選択する。"""
        seed = self._today_seed(user_id)
        rng = random.Random(seed)
        return rng.choice(breeds)

    def _select_today_question_type(self, user_id: uuid.UUID) -> str:
        """日付 + ユーザーID で deterministic に問題形式を選択する。"""
        seed = self._today_seed(user_id) + 999
        rng = random.Random(seed)
        return rng.choice(["photo_to_name", "name_to_photo"])

    def _today_seed(self, user_id: uuid.UUID) -> int:
        """日付 + ユーザーID からシード値を生成する。"""
        today_str = date.today().isoformat()
        combined = f"{today_str}:{user_id}"
        return int(hashlib.sha256(combined.encode()).hexdigest(), 16) % (2**31)

    # ------------------------------------------------------------------
    # Private: レスポンス構築
    # ------------------------------------------------------------------

    def _build_choice_responses(
        self,
        created_choices: list,
        choice_breeds: list,
        question_type: str,
    ) -> list[QuizChoiceResponse]:
        """選択肢のレスポンスを構築する。"""
        breed_map = {b.id: b for b in choice_breeds}
        responses = []
        for choice in created_choices:
            breed = breed_map.get(choice.cat_breed_id)
            if question_type == "photo_to_name":
                responses.append(
                    QuizChoiceResponse(
                        id=choice.cat_breed_id,
                        name=breed.name if breed else None,
                    )
                )
            else:
                responses.append(
                    QuizChoiceResponse(
                        id=choice.cat_breed_id,
                        photo_url=choice.photo_url,
                    )
                )
        return responses

    # ------------------------------------------------------------------
    # POST /quiz/answer
    # ------------------------------------------------------------------

    async def submit_answer(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        question_number: int,
        selected_cat_id: uuid.UUID,
    ) -> AnswerResponse:
        """回答を受け取り、サーバー側で採点・履歴記録する。"""
        # 1. セッション検証
        session = await self.repo.get_session(session_id)
        if session is None:
            raise ValueError("セッションが見つかりません")
        if session.user_id != user_id:
            raise PermissionError("他ユーザーのセッションにはアクセスできません")

        # 2. 問題取得
        question = await self.repo.get_question(session_id, question_number)
        if question is None:
            raise ValueError("問題が見つかりません")

        # 3. 選択肢バリデーション
        choice_cat_ids = await self.repo.get_choice_cat_ids(question.id)
        if selected_cat_id not in choice_cat_ids:
            raise ValueError("選択肢に含まれない猫IDです")

        # 4. 正誤判定
        correct_cat_id = question.correct_cat_breed_id
        is_correct = correct_cat_id == selected_cat_id

        # 5. 回答記録
        await self.repo.create_answer(
            session_id=session_id,
            question_number=question_number,
            selected_cat_breed_id=selected_cat_id,
            is_correct=is_correct,
        )

        # 6. 履歴更新
        if is_correct:
            await self.repo.insert_correct_answer(
                user_id=user_id, cat_breed_id=correct_cat_id
            )
        else:
            await self.repo.upsert_wrong_answer(
                user_id=user_id, cat_breed_id=correct_cat_id
            )

        return AnswerResponse(
            is_correct=is_correct,
            correct_cat_id=correct_cat_id,
        )

    # ------------------------------------------------------------------
    # POST /quiz/sessions/{session_id}/finalize
    # ------------------------------------------------------------------

    async def finalize_session(
        self,
        *,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
    ) -> FinalizeResponse:
        """セッションを完了し、スコアをサーバー側で算出する。"""
        # 1. セッション検証
        session = await self.repo.get_session(session_id)
        if session is None:
            raise ValueError("セッションが見つかりません")
        if session.user_id != user_id:
            raise PermissionError("他ユーザーのセッションにはアクセスできません")
        if session.status == "completed":
            raise ValueError("完了済みのセッションです")

        # 2. 回答数チェック
        total, correct = await self.repo.count_answers(session_id)
        if total < session.total_questions:
            raise ValueError("全問題に回答してください")

        incorrect = total - correct

        # 3. セッション更新
        await self.repo.update_session_status(session, "completed")

        # 4. 結果保存
        result = await self.repo.create_session_result(
            user_id=user_id,
            session_id=session_id,
            source=session.source,
            correct_count=correct,
            incorrect_count=incorrect,
        )

        correct_rate = correct / total if total > 0 else 0.0

        return FinalizeResponse(
            session_id=session_id,
            source=session.source,
            correct_count=correct,
            incorrect_count=incorrect,
            correct_rate=round(correct_rate, 2),
            completed_at=result.completed_at,
        )

    def _build_today_response_from_existing(self, session) -> TodayQuizResponse:
        """既存のセッションからレスポンスを構築する。"""
        question = session.questions[0]
        question_type = question.question_type

        photo_url = None
        cat_name = None
        if question_type == "photo_to_name":
            photo_url = _get_thumbnail_url(question.correct_cat_breed)
        else:
            cat_name = question.correct_cat_breed.name

        choice_responses = []
        for choice in sorted(question.choices, key=lambda c: c.choice_order):
            if question_type == "photo_to_name":
                choice_responses.append(
                    QuizChoiceResponse(
                        id=choice.cat_breed_id,
                        name=choice.cat_breed.name,
                    )
                )
            else:
                choice_responses.append(
                    QuizChoiceResponse(
                        id=choice.cat_breed_id,
                        photo_url=choice.photo_url,
                    )
                )

        return TodayQuizResponse(
            session_id=session.id,
            question_type=question_type,
            question_number=1,
            photo_url=photo_url,
            cat_name=cat_name,
            choices=choice_responses,
        )
