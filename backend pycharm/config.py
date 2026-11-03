import os
from pathlib import Path
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =====================================================================
# CODE-LEVEL API KEYS (Optional: You can paste your keys here directly)
# If .env has a key, .env takes precedence; otherwise this key is used.
# =====================================================================
CODE_OPENAI_API_KEY = ""
CODE_GEMINI_API_KEY = ""


class Settings(BaseSettings):
    APP_NAME: str = "Curriculum & Lesson Plan Microservice"
    APP_ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # ML & RAG Settings
    LLM_PROVIDER: str = "auto"  # 'auto', 'openai', 'gemini', 'ollama'
    OPENAI_API_KEY: str = CODE_OPENAI_API_KEY
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None
    GEMINI_API_KEY: str = CODE_GEMINI_API_KEY
    GEMINI_MODEL_NAME: str = "gemini-3.8-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    CHROMA_DB_PATH: str = "./chroma_db"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "*"]

    @field_validator("OPENAI_API_KEY", mode="before")
    @classmethod
    def validate_openai_key(cls, v):
        if isinstance(v, str) and v.strip():
            return v.strip()
        return CODE_OPENAI_API_KEY

    @field_validator("GEMINI_API_KEY", mode="before")
    @classmethod
    def validate_gemini_key(cls, v):
        if isinstance(v, str) and v.strip():
            return v.strip()
        return CODE_GEMINI_API_KEY

    # Pydantic Settings configuration: ignore extra values found in .env
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
