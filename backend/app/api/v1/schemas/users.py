"""ユーザー統計関連の Pydantic スキーマ（DTO）。

GET /users/me/stats, GET /users/me/sessions/latest のレスポンスを定義する。
"""

import uuid
from datetime import datetime

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# GET /users/me/stats レスポンス
# ---------------------------------------------------------------------------


class UserStatsResponse(BaseModel):
    """ユーザー統計レスポンス。

    correct_answers テーブルの件数（UNIQUE制約により自動でユニーク数）。
    """

    total_correct_breeds: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# GET /users/me/sessions/latest レスポンス
# ---------------------------------------------------------------------------


class LatestSessionResponse(BaseModel):
    """最新セッション結果レスポンス。

    session_results を user_id + source で最新1件取得した結果。
    """

    session_id: uuid.UUID
    source: str
    correct_count: int
    incorrect_count: int
    correct_rate: float
    completed_at: datetime

    model_config = {"from_attributes": True}
