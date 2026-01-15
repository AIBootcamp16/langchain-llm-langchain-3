"""
LLM module - Client Factory
LLM 공급자 설정에 따라 적절한 클라이언트를 반환합니다.
"""

from ..config import get_settings
from .openai_client import get_openai_client, OpenAIClient
from .solar_client import get_solar_client, SolarClient

def get_llm_client():
    """
    설정에 따라 적절한 LLM 클라이언트 인스턴스를 반환합니다.
    
    Returns:
        Union[OpenAIClient, SolarClient]: LLM 클라이언트 인스턴스
    """
    settings = get_settings()
    if settings.llm_provider.lower() == 'solar':
        return get_solar_client()
    elif settings.llm_provider.lower() == 'openai':
        return get_openai_client()
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

__all__ = [
    "get_llm_client",
]