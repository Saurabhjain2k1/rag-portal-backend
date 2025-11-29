from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    ai_provider: str = Field(default="gemini")
    # Local embedding model (HuggingFace)
    local_embed_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="LOCAL_EMBED_MODEL",
    )

    # Gemini (for chat, etc.)
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_chat_model: str = Field(default="models/gemini-2.5-flash", alias="GEMINI_CHAT_MODEL")
    gemini_embed_model: str = Field(default="models/embedding-001", alias="GEMINI_EMBED_MODEL")  # optional now

    chroma_dir: str = Field(default="chroma_data", alias="CHROMA_DIR")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    max_file_size_mb: int = 10
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()
