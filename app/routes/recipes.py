from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.mongo import get_mongo_db
from app.core.qdrant import get_qdrant_client
from app.services.recommendations import RecommendationService

router = APIRouter(prefix="/recipes", tags=["Recipes"])


@router.get("/recommended")
async def get_recommended_recipes(
    user_id: int = Query(..., description="Authenticated user id"),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    mongo_db=Depends(get_mongo_db),
    qdrant_client=Depends(get_qdrant_client),
):
    service = RecommendationService(db, mongo_db, qdrant_client)
    items = await service.get_personalized_recipes(user_id=user_id, limit=limit)
    return {"data": items}


@router.get("/search")
async def search_recipes(
    user_id: int = Query(..., description="Authenticated user id"),
    query: str = Query(..., min_length=2, description="Free-text query"),
    limit: int = Query(12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    mongo_db=Depends(get_mongo_db),
    qdrant_client=Depends(get_qdrant_client),
):
    service = RecommendationService(db, mongo_db, qdrant_client)
    items = await service.search_with_vector_store(
        user_id=user_id,
        query_text=query,
        limit=limit,
    )
    return {"data": items}
