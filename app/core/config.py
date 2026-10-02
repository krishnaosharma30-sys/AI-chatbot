from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Multimodal AI Chatbot"
    
    # Database (defaults to local SQLite; supports PostgreSQL if provided in .env)
    DATABASE_URL: str = "sqlite+aiosqlite:///./chatbot.db"
    SYNC_DATABASE_URL: str = "sqlite:///./chatbot.db"
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v
    
    # API Keys
    AI_API_KEY: str = ""
    WEB_SEARCH_API_KEY: str = ""
    
    # Storage
    STORAGE_PATH: str = "./storage"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
