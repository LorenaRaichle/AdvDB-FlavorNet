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


    # Qdrant
    QDRANT_URL: str | None = "http://qdrant:6333"
    QDRANT_HOST: str | None = None
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int | None = None
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
        host = self.MONGO_HOST or "localhost"
        port = self.MONGO_PORT or 27017
        database = self.MONGO_INITDB_DATABASE or "appdb"
        username = (self.MONGO_INITDB_ROOT_USERNAME or "").strip()
        password = (self.MONGO_INITDB_ROOT_PASSWORD or "").strip()
        auth_source = (self.MONGO_AUTH_SOURCE or "").strip()

        creds = ""
        if username and password:
            creds = f"{username}:{password}@"

        query = ""
        if auth_source and creds:
            query = f"?authSource={auth_source}"

        return f"mongodb://{creds}{host}:{port}/{database}{query}"



    @property
    def qdrant_url(self) -> str:
        """Qdrant endpoint (HTTP or gRPC)."""
        # Prefer explicit host/port wiring (e.g. docker-compose service discovery).
        host = (self.QDRANT_HOST or "").strip()
        if host:
            if host.startswith(("http://", "https://")):
                base = host.rstrip("/")
            else:
                base = f"http://{host}"

            # Only append port if the host didn't already include one.
            host_has_port = ":" in host.split("://")[-1]
            port = self.QDRANT_PORT or 6333
            return base if host_has_port else f"{base}:{port}"

        # Fallback to explicit URL or sensible default for local dev.
        if self.QDRANT_URL:
            return self.QDRANT_URL

        return "http://qdrant:6333"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

# Reusable singleton instance
@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
