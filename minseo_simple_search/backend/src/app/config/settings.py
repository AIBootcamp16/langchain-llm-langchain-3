"""
Application settings using Pydantic Settings
환경변수를 자동으로 로드하고 검증합니다.
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Policy Q&A Agent"
    environment: str = "development"
    debug: bool = True
    port: int = 8000
    
    # Database (MySQL)
    database_url: str = Field(..., validation_alias=AliasChoices("DATABASE_URL", "database_url"))
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Qdrant
    qdrant_url: str = Field(..., validation_alias=AliasChoices("QDRANT_URL", "qdrant_url"))
    qdrant_collection: str = "policies"
    qdrant_api_key: Optional[str] = None
    
    # LLM Provider ('openai' or 'solar')
    llm_provider: str = "openai"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo"
    openai_temperature: float = 0.0
    
    # Solar
    # Upstage(SOLAR) API 키는 프로젝트/환경에 따라 이름이 다를 수 있어 둘 다 허용합니다.
    solar_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("SOLAR_API_KEY", "UPSTAGE_API_KEY"),
    )
    solar_model: str = "solar-1-mini-chat"
    solar_temperature: float = 0.0
    
    # Embedding Model
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
    
    # Web Search
    tavily_api_key: Optional[str] = None
    
    # LangSmith (Observability)
    langsmith_api_key: Optional[str] = None
    langsmith_project: str = "policy-qa-agent"
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
    ]
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Retrieval
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.7
    
    model_config = SettingsConfigDict(
        # 프로젝트 루트의 .env 파일 찾기 (backend/src/app/config/settings.py -> ../../../../.env)
        env_file=str(Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns:
        Settings: Application settings
    """
    return Settings()

