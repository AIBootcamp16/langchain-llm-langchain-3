"""
OpenAI Client
LLM 호출 래퍼
"""

from typing import List, Dict, Any, Optional
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..config import get_settings
from ..config.logger import get_logger
from ..observability import trace_llm_call

logger = get_logger()
settings = get_settings()


class OpenAIClient:
    """
    OpenAI LLM 클라이언트
    
    Attributes:
        model: ChatOpenAI 인스턴스
        model_name: 모델 이름
        temperature: 온도 설정
    """
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.model_name = settings.openai_model
        self.temperature = settings.openai_temperature
        
        try:
            self.model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                openai_api_key=settings.openai_api_key
            )
            
            logger.info(
                "OpenAI client initialized",
                extra={
                    "model": self.model_name,
                    "temperature": self.temperature
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize OpenAI client",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    @trace_llm_call(
        name="generate_response",
        tags=["llm", "openai"],
        metadata={"model": settings.openai_model}
    )
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        메시지 기반 응답 생성
        
        Args:
            messages: 메시지 리스트 [{"role": "user/assistant/system", "content": str}]
            temperature: 온도 (선택)
            max_tokens: 최대 토큰 (선택)
        
        Returns:
            str: 생성된 응답
        """
        try:
            # Convert to LangChain messages
            lc_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:  # user
                    lc_messages.append(HumanMessage(content=content))
            
            # Generate response
            response = self.model.invoke(
                lc_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens
            )
            
            return response.content
            
        except Exception as e:
            logger.error(
                "Error generating response",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        시스템 프롬프트와 사용자 메시지로 응답 생성
        
        Args:
            system_prompt: 시스템 프롬프트
            user_message: 사용자 메시지
            temperature: 온도 (선택)
        
        Returns:
            str: 생성된 응답
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        return self.generate(messages, temperature=temperature)


@lru_cache()
def get_openai_client() -> OpenAIClient:
    """
    Get cached OpenAI client instance
    
    Returns:
        OpenAIClient: Cached client instance
    """
    return OpenAIClient()

