import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas.cat_breeds import (
    CatBreedDetailResponse,
    CatBreedListItem,
    SimilarCatResponse,
)
from app.core.dependencies import DbSession
from app.repositories.cat_breed_repository import CatBreedRepository
from app.services.cat_breed_service import CatBreedService

router = APIRouter(prefix="/cat-breeds", tags=["cat-breeds"])


# ---------------------------------------------------------------------------
# GET /cat-breeds
# ---------------------------------------------------------------------------


@router.get("", response_model=list[CatBreedListItem])
async def get_cat_breeds(
    db: DbSession,
    coat_color_id: uuid.UUID | None = Query(None),
    coat_pattern_id: uuid.UUID | None = Query(None),
    coat_length_id: uuid.UUID | None = Query(None),
) -> list[CatBreedListItem]:
    """猫種一覧を取得する（フィルタ対応）。"""
    repo = CatBreedRepository(db)
    service = CatBreedService(repo)
    return await service.get_breeds(
        coat_color_id=coat_color_id,
        coat_pattern_id=coat_pattern_id,
        coat_length_id=coat_length_id,
    )


# ---------------------------------------------------------------------------
# GET /cat-breeds/{id}
# ---------------------------------------------------------------------------


@router.get("/{breed_id}", response_model=CatBreedDetailResponse)
async def get_cat_breed_detail(
    breed_id: uuid.UUID,
    db: DbSession,
) -> CatBreedDetailResponse:
    """猫種の詳細情報を取得する。"""
    repo = CatBreedRepository(db)
    service = CatBreedService(repo)
    detail = await service.get_breed_detail(breed_id)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cat breed not found",
        )
    return detail


# ---------------------------------------------------------------------------
# GET /cat-breeds/{id}/similar
# ---------------------------------------------------------------------------


@router.get("/{breed_id}/similar", response_model=list[SimilarCatResponse])
async def get_similar_cats(
    breed_id: uuid.UUID,
    db: DbSession,
) -> list[SimilarCatResponse]:
    """類似猫リストを取得する。"""
    repo = CatBreedRepository(db)
    service = CatBreedService(repo)
    return await service.get_similar_breeds(breed_id)
