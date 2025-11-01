from functools import lru_cache

from qdrant_client import QdrantClient

from app.core.config import settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    """Return a cached Qdrant client."""
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.QDRANT_API_KEY or None,
        timeout=30.0,
        prefer_grpc=False,
        check_compatibility=False,
    )
