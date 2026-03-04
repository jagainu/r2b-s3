import uuid

from app.api.v1.schemas.cat_breeds import (
    CatBreedDetailResponse,
    CatBreedListItem,
    CatPhotoResponse,
    CoatAttributeResponse,
    SimilarCatResponse,
)
from app.repositories.cat_breed_repository import CatBreedRepository


def _get_thumbnail_url(breed) -> str | None:
    """display_order=1 の写真URLを取得する。なければ None。"""
    if not breed.photos:
        return None
    sorted_photos = sorted(breed.photos, key=lambda p: p.display_order)
    return sorted_photos[0].photo_url


class CatBreedService:
    def __init__(self, repo: CatBreedRepository) -> None:
        self.repo = repo

    async def get_breeds(
        self,
        *,
        coat_color_id: uuid.UUID | None = None,
        coat_pattern_id: uuid.UUID | None = None,
        coat_length_id: uuid.UUID | None = None,
    ) -> list[CatBreedListItem]:
        """猫種一覧を取得し、DTO に変換する。"""
        has_filter = any([coat_color_id, coat_pattern_id, coat_length_id])

        if has_filter:
            breeds = await self.repo.get_filtered(
                coat_color_id=coat_color_id,
                coat_pattern_id=coat_pattern_id,
                coat_length_id=coat_length_id,
            )
        else:
            breeds = await self.repo.get_all()

        return [
            CatBreedListItem(
                id=b.id,
                name=b.name,
                coat_color=CoatAttributeResponse(
                    id=b.coat_color.id, name=b.coat_color.name
                ),
                coat_pattern=CoatAttributeResponse(
                    id=b.coat_pattern.id, name=b.coat_pattern.name
                ),
                coat_length=CoatAttributeResponse(
                    id=b.coat_length.id, name=b.coat_length.name
                ),
                thumbnail_url=_get_thumbnail_url(b),
            )
            for b in breeds
        ]

    async def get_breed_detail(
        self, breed_id: uuid.UUID
    ) -> CatBreedDetailResponse | None:
        """猫種詳細を取得し、DTO に変換する。"""
        breed = await self.repo.get_by_id(breed_id)
        if breed is None:
            return None

        sorted_photos = sorted(breed.photos, key=lambda p: p.display_order)

        return CatBreedDetailResponse(
            id=breed.id,
            name=breed.name,
            coat_color=CoatAttributeResponse(
                id=breed.coat_color.id, name=breed.coat_color.name
            ),
            coat_pattern=CoatAttributeResponse(
                id=breed.coat_pattern.id, name=breed.coat_pattern.name
            ),
            coat_length=CoatAttributeResponse(
                id=breed.coat_length.id, name=breed.coat_length.name
            ),
            photos=[
                CatPhotoResponse(
                    id=p.id,
                    url=p.photo_url,
                    display_order=p.display_order,
                )
                for p in sorted_photos
            ],
        )

    async def get_similar_breeds(self, breed_id: uuid.UUID) -> list[SimilarCatResponse]:
        """類似猫リストを取得し、DTO に変換する。"""
        similar_cats = await self.repo.get_similar(breed_id)

        return [
            SimilarCatResponse(
                id=sc.similar_cat_breed.id,
                name=sc.similar_cat_breed.name,
                thumbnail_url=_get_thumbnail_url(sc.similar_cat_breed),
            )
            for sc in similar_cats
        ]
