"""クイズ関連の Pydantic スキーマ（DTO）。

POST /quiz/sessions, GET /quiz/today, POST /quiz/answer,
POST /quiz/sessions/{session_id}/finalize のリクエスト・レスポンスを定義する。
correct_cat_breed_id はレスポンスに含めない（サーバーのみ保持）。
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# 共通: 選択肢
# ---------------------------------------------------------------------------


class QuizChoiceResponse(BaseModel):
    """選択肢の統一レスポンス。

    photo_to_name: id + name が設定
    name_to_photo: id + photo_url が設定
    """

    id: uuid.UUID
    name: str | None = None
    photo_url: str | None = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# 問題
# ---------------------------------------------------------------------------


class QuizQuestionResponse(BaseModel):
    """問題1件のレスポンス。

    question_type に応じて photo_url / cat_name / choices の中身が変わる。
    - photo_to_name: photo_url あり, choices は name のみ
    - name_to_photo: cat_name あり, choices は photo_url のみ
    """

    question_number: int
    question_type: str  # "photo_to_name" | "name_to_photo"
    photo_url: str | None = None  # photo_to_name 形式のみ
    cat_name: str | None = None  # name_to_photo 形式のみ
    choices: list[QuizChoiceResponse]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /quiz/sessions レスポンス
# ---------------------------------------------------------------------------


class QuizSessionResponse(BaseModel):
    """POST /quiz/sessions のレスポンス"""

    session_id: uuid.UUID
    questions: list[QuizQuestionResponse]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# GET /quiz/today レスポンス
# ---------------------------------------------------------------------------


class TodayQuizResponse(BaseModel):
    """GET /quiz/today のレスポンス（1問のみ）"""

    session_id: uuid.UUID
    question_type: str
    question_number: int = 1
    photo_url: str | None = None
    cat_name: str | None = None
    choices: list[QuizChoiceResponse]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# POST /quiz/answer リクエスト・レスポンス
# ---------------------------------------------------------------------------


class AnswerRequest(BaseModel):
    """POST /quiz/answer のリクエスト"""

    session_id: uuid.UUID
    question_number: int
    selected_cat_id: uuid.UUID


class AnswerResponse(BaseModel):
    """POST /quiz/answer のレスポンス"""

    is_correct: bool
    correct_cat_id: uuid.UUID


# ---------------------------------------------------------------------------
# POST /quiz/sessions/{session_id}/finalize レスポンス
# ---------------------------------------------------------------------------


class FinalizeResponse(BaseModel):
    """POST /quiz/sessions/{session_id}/finalize のレスポンス"""

    session_id: uuid.UUID
    source: str
    correct_count: int
    incorrect_count: int
    correct_rate: float
    completed_at: datetime
