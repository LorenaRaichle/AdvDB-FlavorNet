from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embeddings import get_embedding_model
from app.repositories.user_repo import UserRepository


class RecommendationService:
    """Coordinates user preferences, MongoDB filtering, and Qdrant similarity search."""

    def __init__(
        self,
        db_session: AsyncSession,
        mongo_db: AsyncIOMotorDatabase,
        qdrant_client: QdrantClient,
    ) -> None:
        self.user_repo = UserRepository(db_session)
        self.mongo_db = mongo_db
        self.qdrant = qdrant_client
        self.collection = settings.QDRANT_COLLECTION

    async def get_personalized_recipes(
        self,
        user_id: int,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        prefs = await self._load_preferences(user_id)
        query = self._build_mongo_query(prefs)

        projection = {
            "_id": 1,
            "slug": 1,
            "title": 1,
            "summary": 1,
            "description": 1,
            "cuisine": 1,
            "course": 1,
            "dietary_tags": 1,
            "allergen_tags": 1,
            "ingredient_tags": 1,
            "ingredients": 1,
            "rating": 1,
        }

        cursor = (
            self.mongo_db.recipes.find(query, projection)
            .sort([("rating.value", -1), ("title", 1)])
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        if not docs:
            return []

        return [self._format_recipe(doc) for doc in docs]

    async def search_with_vector_store(
        self,
        user_id: int,
        query_text: str,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        if not query_text.strip():
            raise HTTPException(status_code=400, detail="Query text cannot be empty.")

        prefs = await self._load_preferences(user_id)
        q_filter = self._build_qdrant_filter(prefs)
        model = get_embedding_model()

        try:
            vector = model.encode([query_text], normalize_embeddings=True)[0].tolist()
        except Exception as err:  # pragma: no cover - model errors surface at runtime
            raise HTTPException(status_code=500, detail="Embedding model failure.") from err

        try:
            hits = self.qdrant.search(
                collection_name=self.collection,
                query_vector=("v_text", vector),
                limit=max(limit, 5),
                query_filter=q_filter,
                with_payload=True,
            )
        except Exception as err:  # pragma: no cover - network errors at runtime
            raise HTTPException(
                status_code=502,
                detail="Vector search service is unavailable.",
            ) from err

        if not hits:
            return []

        slugs_in_order = [hit.payload.get("slug") for hit in hits if hit.payload]
        docs_by_slug = await self._load_recipes_by_slugs(slugs_in_order)

        results: List[Dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            slug = payload.get("slug")
            doc = docs_by_slug.get(slug)
            if not doc:
                # Fall back to payload-only data if Mongo copy is missing.
                results.append(
                    {
                        "id": slug or payload.get("title"),
                        "slug": slug,
                        "title": payload.get("title"),
                        "cuisine": payload.get("cuisine"),
                        "summary": payload.get("summary"),
                        "description": payload.get("summary"),
                        "dietary_tags": payload.get("dietary_tags") or [],
                        "allergen_tags": payload.get("allergen_tags") or [],
                        "ingredient_tags": payload.get("ingredient_tags") or [],
                        "ingredients": payload.get("ingredient_tags") or [],
                        "rating": payload.get("rating_value"),
                        "score": hit.score,
                        "source": "vector-payload",
                    }
                )
                continue

            formatted = self._format_recipe(doc)
            formatted["score"] = hit.score
            results.append(formatted)

        return results[:limit]

    async def _load_preferences(self, user_id: int) -> Dict[str, List[str]]:
        prefs = await self.user_repo.get_user_prefs(user_id)
        if not prefs:
            raise HTTPException(status_code=404, detail="User preferences not found.")

        return {
            "diet_type": self._sanitize_list(prefs.get("diet_type")),
            "allergies": self._sanitize_list(prefs.get("allergies")),
            "dislikes": self._sanitize_list(prefs.get("dislikes")),
        }

    async def _load_recipes_by_slugs(
        self,
        slugs: Iterable[str],
    ) -> Dict[str, Dict[str, Any]]:
        slugs = [s for s in slugs if s]
        if not slugs:
            return {}

        projection = {
            "_id": 1,
            "slug": 1,
            "title": 1,
            "summary": 1,
            "description": 1,
            "cuisine": 1,
            "course": 1,
            "dietary_tags": 1,
            "allergen_tags": 1,
            "ingredient_tags": 1,
            "ingredients": 1,
            "rating": 1,
        }
        cursor = self.mongo_db.recipes.find({"slug": {"$in": slugs}}, projection)
        docs = await cursor.to_list(length=len(slugs))
        return {doc.get("slug"): doc for doc in docs if doc.get("slug")}

    def _build_mongo_query(self, prefs: Dict[str, List[str]]) -> Dict[str, Any]:
        query: Dict[str, Any] = {}

        if prefs["diet_type"]:
            query["dietary_tags"] = {"$all": prefs["diet_type"]}

        if prefs["allergies"]:
            query["allergen_tags"] = {"$nin": prefs["allergies"]}

        if prefs["dislikes"]:
            query["ingredient_tags"] = {"$nin": prefs["dislikes"]}

        return query

    def _build_qdrant_filter(self, prefs: Dict[str, List[str]]) -> Optional[Filter]:
        must: List[FieldCondition] = []
        must_not: List[FieldCondition] = []

        for diet in prefs["diet_type"]:
            must.append(
                FieldCondition(
                    key="dietary_tags",
                    match=MatchValue(value=diet),
                )
            )

        if prefs["allergies"]:
            must_not.append(
                FieldCondition(
                    key="allergen_tags",
                    match=MatchAny(any=prefs["allergies"]),
                )
            )

        if prefs["dislikes"]:
            must_not.append(
                FieldCondition(
                    key="ingredient_tags",
                    match=MatchAny(any=prefs["dislikes"]),
                )
            )

        if not must and not must_not:
            return None

        return Filter(
            must=must or None,
            must_not=must_not or None,
        )

    def _format_recipe(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        ingredients_field = doc.get("ingredients") or []
        ingredients: List[str] = []
        if isinstance(ingredients_field, list):
            for item in ingredients_field:
                if isinstance(item, dict):
                    candidate = item.get("raw") or item.get("name")
                    if candidate:
                        ingredients.append(candidate)
                elif isinstance(item, str):
                    ingredients.append(item)

        if not ingredients:
            ingredients = doc.get("ingredient_tags") or []

        rating = doc.get("rating") or {}
        doc_id = doc.get("_id")
        if isinstance(doc_id, ObjectId):
            doc_id = str(doc_id)
        elif doc_id is not None:
            doc_id = str(doc_id)

        return {
            "id": doc_id,
            "slug": doc.get("slug"),
            "title": doc.get("title"),
            "summary": doc.get("summary"),
            "description": doc.get("description"),
            "cuisine": doc.get("cuisine"),
            "course": doc.get("course"),
            "dietary_tags": doc.get("dietary_tags") or [],
            "allergen_tags": doc.get("allergen_tags") or [],
            "ingredient_tags": doc.get("ingredient_tags") or [],
            "ingredients": ingredients,
            "rating": rating.get("value"),
            "rating_count": rating.get("count"),
            "score": None,
            "source": "mongo",
        }

    @staticmethod
    def _sanitize_list(value: Optional[Iterable[str]]) -> List[str]:
        return [item.strip().lower() for item in (value or []) if isinstance(item, str) and item.strip()]
