"""クイズ関連のエンドポイント。

POST /quiz/sessions - クイズセッション生成（10問一括）
GET /quiz/today - 今日の一匹
POST /quiz/answer - 回答送信・サーバー採点・履歴記録
POST /quiz/sessions/{session_id}/finalize - セッション完了・スコア算出
"""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.v1.schemas.quiz import (
    AnswerRequest,
    AnswerResponse,
    FinalizeResponse,
    QuizSessionResponse,
    TodayQuizResponse,
)
from app.core.dependencies import CsrfVerified, CurrentUser, DbSession
from app.repositories.quiz_repository import QuizRepository
from app.services.quiz_service import QuizService

router = APIRouter(prefix="/quiz", tags=["quiz"])


# ---------------------------------------------------------------------------
# POST /quiz/sessions  🔒 ✅CSRF
# ---------------------------------------------------------------------------


@router.post(
    "/sessions",
    response_model=QuizSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_quiz_session(
    db: DbSession,
    current_user: CurrentUser,
    _csrf: CsrfVerified,
) -> QuizSessionResponse:
    """クイズセッションを作成し、10問を一括生成する。"""
    repo = QuizRepository(db)
    service = QuizService(repo)
    return await service.create_quiz_session(current_user.id)


# ---------------------------------------------------------------------------
# GET /quiz/today  🔒
# ---------------------------------------------------------------------------


@router.get("/today", response_model=TodayQuizResponse)
async def get_today_quiz(
    db: DbSession,
    current_user: CurrentUser,
) -> TodayQuizResponse:
    """今日の一匹クイズを取得する。"""
    repo = QuizRepository(db)
    service = QuizService(repo)
    return await service.get_today_quiz(current_user.id)


# ---------------------------------------------------------------------------
# POST /quiz/answer  🔒 ✅CSRF
# ---------------------------------------------------------------------------


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    body: AnswerRequest,
    db: DbSession,
    current_user: CurrentUser,
    _csrf: CsrfVerified,
) -> AnswerResponse:
    """クイズ回答を送信する。正解判定はサーバー側で行う。"""
    repo = QuizRepository(db)
    service = QuizService(repo)
    try:
        return await service.submit_answer(
            user_id=current_user.id,
            session_id=body.session_id,
            question_number=body.question_number,
            selected_cat_id=body.selected_cat_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="アクセス権がありません"
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="この問題にはすでに回答済みです",
        )


# ---------------------------------------------------------------------------
# POST /quiz/sessions/{session_id}/finalize  🔒 ✅CSRF
# ---------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/finalize",
    response_model=FinalizeResponse,
)
async def finalize_session(
    session_id: uuid.UUID,
    db: DbSession,
    current_user: CurrentUser,
    _csrf: CsrfVerified,
) -> FinalizeResponse:
    """セッションを完了し、結果をサーバー側で算出する。"""
    repo = QuizRepository(db)
    service = QuizService(repo)
    try:
        return await service.finalize_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="アクセス権がありません"
        )
