import uuid

from pydantic import BaseModel


class MasterItemResponse(BaseModel):
    """マスターデータの共通レスポンス"""

    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
