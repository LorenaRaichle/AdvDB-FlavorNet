from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, ScoredPoint
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.embeddings import get_embedding_model
from app.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# Basic canonicalized animal-product blockers for vegan enforcement.
NON_VEGAN_TERMS = {
    "beef",
    "pork",
    "bacon",
    "ham",
    "sausage",
    "chicken",
    "turkey",
    "duck",
    "lamb",
    "mutton",
    "veal",
    "fish",
    "salmon",
    "tuna",
    "cod",
    "anchovy",
    "anchovies",
    "sardine",
    "sardines",
    "trout",
    "mackerel",
    "shrimp",
    "prawn",
    "prawns",
    "crab",
    "crabmeat",
    "lobster",
    "oyster",
    "oysters",
    "clam",
    "clams",
    "mussel",
    "mussels",
    "scallop",
    "scallops",
    "gelatin",
    "gelatine",
    "lard",
    "tallow",
    "whey",
    "casein",
    "egg",
    "eggs",
    "egg yolk",
    "egg yolks",
    "egg white",
    "egg whites",
    "milk",
    "whole milk",
    "skim milk",
    "butter",
    "buttermilk",
    "cream",
    "heavy cream",
    "sour cream",
    "yogurt",
    "cheese",
    "mozzarella",
    "cheddar",
    "parmesan",
    "gouda",
    "feta",
    "ricotta",
    "goat cheese",
    "blue cheese",
    "honey",
}


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
        self._prefs: Dict[str, List[str]] = {}

    async def get_personalized_recipes(
        self,
        user_id: int,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        prefs = await self._load_preferences(user_id)
        self._prefs = prefs  # cache for downstream filtering
        q_filter = self._build_qdrant_filter(prefs)
        profile_query = self._build_profile_query(prefs)

        try:
            vector = self._embed_query_text(profile_query)
            search_limit = max(limit * 3, 20)
            hits = self._run_vector_search(vector, q_filter, search_limit)
            items = await self._build_results_from_hits(hits, limit)
            if items:
                return items
        except HTTPException as err:
            if err.status_code == 404:
                raise
            # other HTTP errors (embedding/Qdrant) fall back to MongoDB
        except Exception:
            pass

        return await self._load_top_mongo_recipes(prefs, limit)

    async def search_with_vector_store(
        self,
        user_id: int,
        query_text: str,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        if not query_text.strip():
            raise HTTPException(status_code=400, detail="Query text cannot be empty.")

        prefs = await self._load_preferences(user_id)
        self._prefs = prefs  # cache for downstream filtering
        q_filter = self._build_qdrant_filter(prefs)
        vector = self._embed_query_text(query_text)
        search_limit = max(limit * 3, 20)
        hits = self._run_vector_search(vector, q_filter, search_limit)
        return await self._build_results_from_hits(hits, limit)

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
            "flavour_tags": 1,
            "technique_tags": 1,
            "source_url": 1,
            "images": 1,
            "image": 1,
            "nutrition": 1,
            "nutritional_info": 1,
        }
        cursor = self.mongo_db.recipes.find({"slug": {"$in": slugs}}, projection)
        docs = await cursor.to_list(length=len(slugs))
        return {doc.get("slug"): doc for doc in docs if doc.get("slug")}

    def _build_mongo_query(self, prefs: Dict[str, List[str]]) -> Dict[str, Any]:
        query: Dict[str, Any] = {}

        if prefs["diet_type"]:
            query["dietary_tags"] = {"$all": prefs["diet_type"]}

        nin_ingredients: List[str] = []
        if prefs["allergies"]:
            # Exclude recipes that contain allergens either in explicit allergen_tags
            # or in the broader ingredient_tags list.
            query["allergen_tags"] = {"$nin": prefs["allergies"]}
            nin_ingredients.extend(prefs["allergies"])

        if prefs["dislikes"]:
            nin_ingredients.extend(prefs["dislikes"])

        if nin_ingredients:
            query["ingredient_tags"] = {"$nin": nin_ingredients}

        return query

    def _build_qdrant_filter(self, prefs: Dict[str, List[str]]) -> Optional[Filter]:
        must: List[FieldCondition] = []
        must_not: List[FieldCondition] = []

        for diet in prefs["diet_type"]:
            must.append(
                FieldCondition(
                    key="dietary_tags",
                    match=MatchAny(any=[diet]),
                )
            )

        if prefs["allergies"]:
            allergy_match = MatchAny(any=prefs["allergies"])
            must_not.append(FieldCondition(key="allergen_tags", match=allergy_match))
            must_not.append(FieldCondition(key="ingredient_tags", match=allergy_match))

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

    def _build_profile_query(self, prefs: Dict[str, List[str]]) -> str:
        segments: List[str] = []
        if prefs["diet_type"]:
            segments.append(f"{', '.join(prefs['diet_type'])} friendly recipes")
        if prefs["allergies"]:
            segments.append(f"free from {', '.join(prefs['allergies'])}")
        if prefs["dislikes"]:
            segments.append(f"avoid {', '.join(prefs['dislikes'])}")
        return ". ".join(segments) or "popular personalized recipes"

    def _embed_query_text(self, text: str) -> List[float]:
        model = get_embedding_model()
        try:
            return model.encode([text], normalize_embeddings=True)[0].tolist()
        except Exception as err:  # pragma: no cover
            raise HTTPException(status_code=500, detail="Embedding model failure.") from err

    def _run_vector_search(
        self,
        vector: List[float],
        q_filter: Optional[Filter],
        limit: int,
    ) -> List[ScoredPoint]:
        try:
            return self.qdrant.search(
                collection_name=self.collection,
                query_vector=("v_text", vector),
                limit=max(limit, 5),
                query_filter=q_filter,
                with_payload=True,
            )
        except Exception as err:  # pragma: no cover
            # Log with both logger and stderr to ensure visibility in container logs.
            logger.exception(
                "Qdrant vector search failed",
                extra={
                    "collection": self.collection,
                    "limit": limit,
                    "has_filter": bool(q_filter),
                    "vector_dim": len(vector) if vector else None,
                },
            )
            import sys, traceback

            print(
                f"[vector_search_error] collection={self.collection} limit={limit} "
                f"has_filter={bool(q_filter)} vector_dim={len(vector) if vector else None}",
                file=sys.stderr,
            )
            traceback.print_exc()
            raise HTTPException(
                status_code=502,
                detail="Vector search service is unavailable.",
            ) from err

    async def _build_results_from_hits(
        self,
        hits: List[ScoredPoint],
        limit: int,
    ) -> List[Dict[str, Any]]:
        if not hits:
            return []

        slugs_in_order = [hit.payload.get("slug") for hit in hits if hit.payload]
        docs_by_slug = await self._load_recipes_by_slugs(slugs_in_order)

        results: List[Dict[str, Any]] = []
        for hit in hits:
            payload = hit.payload or {}
            slug = payload.get("slug")
            doc = docs_by_slug.get(slug)

            # Prefer Mongo doc (authoritative tags); if absent, fall back to payload.
            candidate = None
            if doc:
                formatted = self._format_recipe(doc)
                formatted["source"] = "mongo"
                candidate = formatted
            else:
                formatted = self._format_payload_recipe(payload)
                candidate = formatted

            # Hard-filter against preferences to avoid allergen/diet leaks when payload tags are incomplete.
            if not self._matches_prefs(candidate):
                continue

            # Additional safeguards on early hits: scan ingredient text for allergens/dislikes and non-vegan terms.
            if len(results) < 20:
                if self._violates_ingredient_text(candidate) or self._violates_diet_terms(candidate):
                    continue

            candidate["score"] = hit.score
            results.append(candidate)

            if len(results) >= limit:
                break

        return results

    async def _load_top_mongo_recipes(
        self,
        prefs: Dict[str, List[str]],
        limit: int,
    ) -> List[Dict[str, Any]]:
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
            "flavour_tags": 1,
            "technique_tags": 1,
            "source_url": 1,
        }
        cursor = (
            self.mongo_db.recipes.find(query, projection)
            .sort([("rating.value", -1), ("title", 1)])
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [self._format_recipe(doc) for doc in docs]

    def _format_payload_recipe(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        ingredients = payload.get("ingredient_tags") or []
        steps = payload.get("steps") or []
        if isinstance(steps, str):
            steps = [s.strip() for s in steps.split("\n") if s.strip()]
        images_field = payload.get("images") or payload.get("image") or payload.get("image_url")
        images: List[str] = []
        if isinstance(images_field, list):
            images = [str(img) for img in images_field if img]
        elif isinstance(images_field, str):
            images = [images_field]

        nutrition = payload.get("nutrition") or payload.get("nutritional_info")
        return {
            "id": payload.get("slug") or payload.get("title"),
            "slug": payload.get("slug"),
            "title": payload.get("title"),
            "summary": payload.get("summary"),
            "description": payload.get("summary"),
            "cuisine": payload.get("cuisine"),
            "course": payload.get("course"),
            "dietary_tags": payload.get("dietary_tags") or [],
            "allergen_tags": payload.get("allergen_tags") or [],
            "ingredient_tags": ingredients,
            "ingredients": ingredients,
            "steps": steps,
            "images": images,
            "nutrition": nutrition,
            "flavour_tags": payload.get("flavour_tags") or [],
            "technique_tags": payload.get("technique_tags") or [],
            "rating": payload.get("rating_value"),
            "rating_count": payload.get("rating_count"),
            "source_url": payload.get("source_url"),
            "source": "vector-payload",
        }

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

        description = doc.get("description") or doc.get("summary")
        steps_field = doc.get("steps") or doc.get("instructions") or []
        steps: List[str] = []
        if isinstance(steps_field, list):
            for step in steps_field:
                if isinstance(step, str):
                    cleaned = step.strip()
                    if cleaned:
                        steps.append(cleaned)
        elif isinstance(steps_field, str):
            steps = [line.strip() for line in steps_field.split("\n") if line.strip()]

        images_field = doc.get("images") or doc.get("image")
        images: List[str] = []
        if isinstance(images_field, list):
            images = [str(img) for img in images_field if img]
        elif isinstance(images_field, str):
            images = [images_field]

        nutrition = doc.get("nutrition") or doc.get("nutritional_info")

        return {
            "id": doc_id,
            "slug": doc.get("slug"),
            "title": doc.get("title"),
            "summary": doc.get("summary"),
            "description": description,
            "cuisine": doc.get("cuisine"),
            "course": doc.get("course"),
            "dietary_tags": doc.get("dietary_tags") or [],
            "allergen_tags": doc.get("allergen_tags") or [],
            "ingredient_tags": doc.get("ingredient_tags") or [],
            "ingredients": ingredients,
            "steps": steps,
            "images": images,
            "nutrition": nutrition,
            "flavour_tags": doc.get("flavour_tags") or [],
            "technique_tags": doc.get("technique_tags") or [],
            "rating": rating.get("value"),
            "rating_count": rating.get("count"),
            "source_url": doc.get("source_url"),
            "score": None,
            "source": "mongo",
        }

    @staticmethod
    def _sanitize_list(value: Optional[Iterable[str]]) -> List[str]:
        return [item.strip().lower() for item in (value or []) if isinstance(item, str) and item.strip()]

    def _matches_prefs(self, recipe: Dict[str, Any]) -> bool:
        """Ensure recipe satisfies dietary inclusion and allergy/dislike exclusions."""
        if not isinstance(recipe, dict):
            return False

        diet = self._sanitize_list(recipe.get("dietary_tags"))
        allergens = self._sanitize_list(recipe.get("allergen_tags"))
        ingredients = self._sanitize_list(recipe.get("ingredient_tags") or recipe.get("ingredients"))

        # All required diets must be present (if any).
        if self._prefs.get("diet_type"):
            for required in self._prefs["diet_type"]:
                if required not in diet:
                    return False

        # No allergies in allergens or ingredients.
        for allergy in self._prefs.get("allergies", []):
            if allergy in allergens or allergy in ingredients:
                return False

        # Dislikes excluded via ingredient tags.
        for dislike in self._prefs.get("dislikes", []):
            if dislike in ingredients:
                return False

        return True

    def _violates_ingredient_text(self, recipe: Dict[str, Any]) -> bool:
        """Catch obvious allergen/dislike strings in ingredients text when tags are incomplete."""
        prefs_allergies = set(self._prefs.get("allergies", []))
        prefs_dislikes = set(self._prefs.get("dislikes", []))
        if not prefs_allergies and not prefs_dislikes:
            return False

        ingredients_field = recipe.get("ingredients") or recipe.get("ingredient_tags")
        texts: List[str] = []
        if isinstance(ingredients_field, list):
            texts = [str(item).lower() for item in ingredients_field if item]
        elif isinstance(ingredients_field, str):
            texts = [ingredients_field.lower()]

        haystack = " | ".join(texts)
        for term in prefs_allergies.union(prefs_dislikes):
            if term.lower() in haystack:
                return True
        return False

    def _violates_diet_terms(self, recipe: Dict[str, Any]) -> bool:
        """Reject recipes that conflict with diet when tags alone are insufficient."""
        diet = set(self._prefs.get("diet_type") or [])
        if "vegan" not in diet:
            return False

        ingredients_field = recipe.get("ingredients") or recipe.get("ingredient_tags")
        texts: List[str] = []
        if isinstance(ingredients_field, list):
            texts = [str(item).lower() for item in ingredients_field if item]
        elif isinstance(ingredients_field, str):
            texts = [ingredients_field.lower()]

        haystack = " | ".join(texts)
        for term in NON_VEGAN_TERMS:
            if term in haystack:
                return True
        return False
