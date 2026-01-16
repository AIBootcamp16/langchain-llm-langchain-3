"""
LangSmith Client 초기화 및 관리
LangSmith API와의 통신을 담당합니다.
"""

import os
from typing import Optional
from functools import lru_cache

from langsmith import Client

from ..config import get_settings
from ..config.logger import get_logger

logger = get_logger()


class LangSmithClient:
    """
    LangSmith 클라이언트 래퍼
    
    Attributes:
        enabled: 트레이싱 활성화 여부
        client: LangSmith 클라이언트 인스턴스
        project_name: 프로젝트 이름
    """
    
    def __init__(self):
        """Initialize LangSmith client"""
        settings = get_settings()
        
        self.enabled = settings.langsmith_tracing
        self.project_name = settings.langsmith_project
        self.client: Optional[Client] = None
        
        if self.enabled and settings.langsmith_api_key:
            try:
                self.client = Client(
                    api_key=settings.langsmith_api_key,
                    api_url=settings.langsmith_endpoint
                )
                
                # Set environment variables for langchain tracing
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
                os.environ["LANGCHAIN_PROJECT"] = self.project_name
                os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
                
                logger.info(
                    "LangSmith client initialized",
                    extra={
                        "project": self.project_name,
                        "endpoint": settings.langsmith_endpoint
                    }
                )
            except Exception as e:
                logger.error(
                    "Failed to initialize LangSmith client",
                    extra={"error": str(e)},
                    exc_info=True
                )
                self.enabled = False
                self.client = None
        else:
            logger.info("LangSmith tracing is disabled")
    
    def get_client(self) -> Optional[Client]:
        """
        Get LangSmith client instance
        
        Returns:
            Optional[Client]: Client instance if enabled, None otherwise
        """
        return self.client if self.enabled else None
    
    def is_enabled(self) -> bool:
        """
        Check if LangSmith is enabled
        
        Returns:
            bool: True if enabled, False otherwise
        """
        return self.enabled and self.client is not None


@lru_cache()
def get_langsmith_client() -> LangSmithClient:
    """
    Get cached LangSmith client instance
    
    Returns:
        LangSmithClient: Cached client instance
    """
    return LangSmithClient()

