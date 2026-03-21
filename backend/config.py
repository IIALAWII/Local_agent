"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object; values are read from .env or environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ── Ollama / LLM ─────────────────────────────────────────────────────────
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "gpt-oss:20b"
    llm_temperature: float = 0.7

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_host: str = "chromadb"
    chroma_port: int = 8000
    chroma_collection: str = "agent_memory"

    # ── Google OAuth2 ─────────────────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:3000/auth/callback"

    # ── App ───────────────────────────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"
    secret_key: str = "change-me-in-production"


settings = Settings()
