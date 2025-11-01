from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # PostgreSQL
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    PGHOST: str = "postgres"
    PGPORT: int = 55433

    # MongoDB 
    MONGO_INITDB_ROOT_USERNAME: str | None = None
    MONGO_INITDB_ROOT_PASSWORD: str | None = None
    MONGO_INITDB_DATABASE: str | None = None
    MONGO_HOST: str | None = "localhost"
    MONGO_PORT: int | None = 27017
    MONGO_AUTH_SOURCE: str | None = "admin"

    # Neo4j
    APP_NEO4J_URI: str | None = "bolt://localhost:7687"
    APP_NEO4J_USER: str | None = "neo4j"
    APP_NEO4J_PASSWORD: str | None = "password"

    # Qdrant
    QDRANT_URL: str | None = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "recipes"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Misc / App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_NAME: str = "FlavorNet"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # --- Helper Properties ---
    @property
    def postgres_url(self) -> str:
        """Async SQLAlchemy/Postgres URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@{self.PGHOST}:{self.PGPORT}/"
            f"{self.POSTGRES_DB}"
        )

    @property
    def mongo_url(self) -> str:
        """Standard Mongo connection string."""
        if self.MONGO_INITDB_ROOT_USERNAME and self.MONGO_INITDB_ROOT_PASSWORD:
            host = self.MONGO_HOST or "localhost"
            port = self.MONGO_PORT or 27017
            database = self.MONGO_INITDB_DATABASE or "admin"
            auth_source = self.MONGO_AUTH_SOURCE

            query = ""
            if auth_source:
                query = f"?authSource={auth_source}"

            return (
                f"mongodb://{self.MONGO_INITDB_ROOT_USERNAME}:"
                f"{self.MONGO_INITDB_ROOT_PASSWORD}@{host}:{port}/"
                f"{database}{query}"
            )

        host = self.MONGO_HOST or "localhost"
        port = self.MONGO_PORT or 27017
        return f"mongodb://{host}:{port}"

    @property
    def neo4j_url(self) -> str:
        """Bolt URI for Neo4j driver."""
        return self.APP_NEO4J_URI

    @property
    def qdrant_url(self) -> str:
        """Qdrant endpoint (HTTP or gRPC)."""
        return self.QDRANT_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Reusable singleton instance
@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
