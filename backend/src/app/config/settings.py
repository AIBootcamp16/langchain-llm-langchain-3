"""
Application settings using Pydantic Settings
환경변수를 자동으로 로드하고 검증합니다.
"""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Policy Q&A Agent"
    environment: str = "development"
    debug: bool = True
    port: int = 8000
    
    # Database (MySQL)
    database_url: str
    db_echo: bool = False
    db_pool_size: int = 10
    db_max_overflow: int = 20
    
    # Qdrant
    qdrant_url: str
    qdrant_collection: str = "policies"
    qdrant_api_key: Optional[str] = None
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"  # 128K context, 저렴한 비용
    openai_temperature: float = 0.0
    
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
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Retrieval
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.7
    
    model_config = SettingsConfigDict(
        env_file=".env",
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

