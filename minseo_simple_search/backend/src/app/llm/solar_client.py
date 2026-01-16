"""
Solar Client
"""
from functools import lru_cache
from typing import Dict, Any, List, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_upstage import ChatUpstage

from ..config import get_settings
from ..config.logger import get_logger
from ..observability import trace_llm_call

settings = get_settings()
logger = get_logger()

class SolarClient:
    """
    Solar LLM 클라이언트
    Upstage(SOLAR) Chat 모델을 래핑합니다.

    주의:
    - `langchain_community.chat_models.solar`는 패키지 import 과정에서 다른 provider(예: anthropic) 모듈까지
      함께 import될 수 있고, Pydantic 버전 조합에 따라 부팅 단계에서 에러가 발생할 수 있습니다.
    - 본 프로젝트는 이미 `langchain-upstage`를 사용 가능하므로 `ChatUpstage`를 사용합니다.
    """
    def __init__(self):
        """Initialize Solar client"""
        if not settings.solar_api_key:
            raise ValueError("SOLAR_API_KEY is not set. Please add it to your .env file.")
        
        try:
            # langchain-upstage의 기본 모델명은 `solar-mini`류이지만,
            # 기존 설정값(`solar-1-mini-chat`)도 그대로 전달해 호환성을 유지합니다.
            self.model_name = settings.solar_model
            self.temperature = settings.solar_temperature

            self.model = ChatUpstage(
                model=self.model_name,
                temperature=self.temperature,
                upstage_api_key=settings.solar_api_key,
            )
            logger.info("Solar client initialized", extra={"model": self.model_name})
        except Exception as e:
            logger.error("Failed to initialize Solar client", extra={"error": str(e)})
            self.model = None

    @trace_llm_call(
        name="solar_generate",
        tags=["llm", "solar"],
        metadata={"model": settings.solar_model}
    )
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        메시지 기반 응답 생성
        """
        if not self.model:
            logger.error("Cannot generate response, Solar client not initialized")
            return "Error: Solar client is not available."

        try:
            lc_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    lc_messages.append(SystemMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))
                else:
                    lc_messages.append(HumanMessage(content=content))

            invoke_kwargs: Dict[str, Any] = {"temperature": temperature or self.temperature}
            if max_tokens is not None:
                # Upstage는 OpenAI와 동일하게 max_tokens를 지원합니다.
                invoke_kwargs["max_tokens"] = max_tokens

            response = self.model.invoke(lc_messages, **invoke_kwargs)
            return response.content
        except Exception as e:
            logger.error("Error generating Solar response", extra={"error": str(e)})
            raise

    def generate_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None
    ) -> str:
        """
        시스템 프롬프트와 함께 생성 (generate 메서드 사용)
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.generate(messages, temperature=temperature)

@lru_cache()
def get_solar_client() -> SolarClient:
    """
    Get cached Solar client instance
    
    Returns:
        SolarClient: Cached client instance
    """
    return SolarClient()