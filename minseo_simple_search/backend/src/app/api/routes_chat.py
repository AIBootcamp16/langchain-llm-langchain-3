"""
Chat API Routes
Q&A 멀티턴 대화 엔드포인트
"""

import uuid
from fastapi import APIRouter, HTTPException

from ..agent import AgentController
from ..domain.chat import ChatRequest, ChatResponse, SessionResetResponse
from ..config.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Q&A 채팅",
    description="특정 정책에 대한 멀티턴 Q&A를 수행합니다.",
    tags=["Chat"]
)
async def chat(request: ChatRequest):
    """
    Q&A 채팅 API
    
    **기능:**
    - 특정 정책에 대한 상세 질의응답
    - Qdrant + MySQL 기반 RAG
    - 필요시 DuckDuckGo 웹 검색
    - 모든 답변에 근거(evidence) 제공
    
    **워크플로우:**
    1. classify_query: 질문 분류 (웹 검색 필요 여부)
    2. retrieve_from_db: Qdrant 벡터 검색
    3. check_sufficiency: 근거 충분성 판단
    4. web_search: (필요시) 웹 검색
    5. generate_answer: LLM으로 답변 생성
    
    **예시:**
    ```json
    {
      "session_id": "abc-123",
      "policy_id": 1,
      "message": "지원 금액은 얼마인가요?"
    }
    ```
    """
    try:
        # Generate session_id if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Run Q&A workflow
        result = AgentController.run_qa(
            session_id=session_id,
            policy_id=request.policy_id,
            user_message=request.message
        )
        
        return ChatResponse(**result)
        
    except Exception as e:
        logger.error(
            "Error in chat endpoint",
            extra={
                "policy_id": request.policy_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/session/reset",
    response_model=SessionResetResponse,
    summary="세션 초기화",
    description="특정 세션의 대화 이력을 초기화합니다.",
    tags=["Chat"]
)
async def reset_session(session_id: str):
    """
    세션 초기화 API
    
    **기능:**
    - 세션 삭제 (대화 이력, 슬롯, 체크리스트 결과 포함)
    - 홈으로 돌아갈 때 호출
    
    **예시:**
    ```
    POST /session/reset?session_id=abc-123
    ```
    """
    try:
        success = AgentController.reset_session(session_id)
        
        if success:
            return SessionResetResponse(
                session_id=session_id,
                success=True,
                message="세션이 초기화되었습니다."
            )
        else:
            return SessionResetResponse(
                session_id=session_id,
                success=False,
                message="세션을 찾을 수 없거나 이미 삭제되었습니다."
            )
        
    except Exception as e:
        logger.error(
            "Error resetting session",
            extra={"session_id": session_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"세션 초기화 중 오류가 발생했습니다: {str(e)}"
        )

