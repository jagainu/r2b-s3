from fastapi import APIRouter

from app.api.v1.schemas.masters import MasterItemResponse
from app.core.dependencies import DbSession
from app.repositories.master_repository import MasterRepository

router = APIRouter(prefix="/masters", tags=["masters"])


# ---------------------------------------------------------------------------
# GET /masters/coat-colors
# ---------------------------------------------------------------------------


@router.get("/coat-colors", response_model=list[MasterItemResponse])
async def get_coat_colors(db: DbSession) -> list[MasterItemResponse]:
    """毛色マスター一覧を取得する。"""
    repo = MasterRepository(db)
    colors = await repo.get_coat_colors()
    return [MasterItemResponse.model_validate(c) for c in colors]


# ---------------------------------------------------------------------------
# GET /masters/coat-patterns
# ---------------------------------------------------------------------------


@router.get("/coat-patterns", response_model=list[MasterItemResponse])
async def get_coat_patterns(db: DbSession) -> list[MasterItemResponse]:
    """模様マスター一覧を取得する。"""
    repo = MasterRepository(db)
    patterns = await repo.get_coat_patterns()
    return [MasterItemResponse.model_validate(p) for p in patterns]


# ---------------------------------------------------------------------------
# GET /masters/coat-lengths
# ---------------------------------------------------------------------------


@router.get("/coat-lengths", response_model=list[MasterItemResponse])
async def get_coat_lengths(db: DbSession) -> list[MasterItemResponse]:
    """毛の長さマスター一覧を取得する。"""
    repo = MasterRepository(db)
    lengths = await repo.get_coat_lengths()
    return [MasterItemResponse.model_validate(item) for item in lengths]
