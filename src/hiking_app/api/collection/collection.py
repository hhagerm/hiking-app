from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query


from hiking_app.db import CollectionRepository
from hiking_app.core.dependencies import get_collection_repo, get_current_user
from hiking_app.models import User
from .response import CollectionListResponse

collection_router = APIRouter()

@collection_router.post(
    "/claim",
    status_code=201,
    summary="Collect specific POI",
)
async def claim_poi(
    osm_type: Annotated[Literal["n", "w", "r"], Query()],
    osm_id: Annotated[int, Query(gt=0)],
    user: User = Depends(get_current_user),
    repo: CollectionRepository = Depends(get_collection_repo),
    ):
    return await repo.claim_poi(user.id, osm_type, osm_id)

@collection_router.post(
    "/unclaim",
    status_code=204,
    summary="Uncollect specific POI",
)
async def unclaim_poi(
    osm_type: Annotated[Literal["n", "w", "r"], Query()],
    osm_id: Annotated[int, Query(gt=0)],
    user: User = Depends(get_current_user),
    repo: CollectionRepository = Depends(get_collection_repo),
    ):
    return await repo.unclaim_poi(user.id, osm_type, osm_id)

@collection_router.get(
    "/list",
    response_model=list[CollectionListResponse],
    summary="Get list of collected POIs",
)
async def list_collection(
    user: User = Depends(get_current_user),
    repo: CollectionRepository = Depends(get_collection_repo),
    ):
    return await repo.list_claims(user.id)