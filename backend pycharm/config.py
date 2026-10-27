import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    APP_NAME: str = "Curriculum & Lesson Plan Microservice"
    APP_ENV: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # ML & RAG Settings
    LLM_PROVIDER: str = "auto"  # 'auto', 'openai', 'gemini', 'ollama'
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL_NAME: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Optional[str] = None
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-1.5-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    CHROMA_DB_PATH: str = "./chroma_db"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "*"]

    # Pydantic Settings configuration: ignore extra values found in .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()