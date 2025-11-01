from functools import lru_cache
from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_client() -> AsyncIOMotorClient:
    """Return a cached Mongo client."""
    return AsyncIOMotorClient(settings.mongo_url)


def _get_database_name() -> str:
    """Resolve the database name with a sensible default."""
    return settings.MONGO_INITDB_DATABASE or "appdb"


async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    FastAPI dependency that yields the Mongo database handle.

    The underlying client is cached at module level so connections are reused.
    """
    client = _get_client()
    db = client[_get_database_name()]
    yield db
