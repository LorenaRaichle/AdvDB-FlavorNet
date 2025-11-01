from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence-transformer model."""
    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
