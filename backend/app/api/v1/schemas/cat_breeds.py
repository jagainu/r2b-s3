import uuid

from pydantic import BaseModel


class CoatAttributeResponse(BaseModel):
    """毛色・模様・毛の長さの共通レスポンス"""

    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class CatBreedListItem(BaseModel):
    """猫種一覧のアイテム（GET /cat-breeds）"""

    id: uuid.UUID
    name: str
    coat_color: CoatAttributeResponse
    coat_pattern: CoatAttributeResponse
    coat_length: CoatAttributeResponse
    thumbnail_url: str | None = None

    model_config = {"from_attributes": True}


class CatPhotoResponse(BaseModel):
    """猫写真レスポンス"""

    id: uuid.UUID
    url: str
    display_order: int

    model_config = {"from_attributes": True}


class CatBreedDetailResponse(BaseModel):
    """猫種詳細レスポンス（GET /cat-breeds/{id}）"""

    id: uuid.UUID
    name: str
    coat_color: CoatAttributeResponse
    coat_pattern: CoatAttributeResponse
    coat_length: CoatAttributeResponse
    photos: list[CatPhotoResponse]

    model_config = {"from_attributes": True}


class SimilarCatResponse(BaseModel):
    """類似猫レスポンス（GET /cat-breeds/{id}/similar）"""

    id: uuid.UUID
    name: str
    thumbnail_url: str | None = None

    model_config = {"from_attributes": True}
