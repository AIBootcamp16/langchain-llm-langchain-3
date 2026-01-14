"""
Chat API Routes
Q&A 멀티턴 대화 엔드포인트
"""

import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agent import AgentController
from ..domain.chat import ChatRequest, ChatResponse, SessionResetResponse
from ..config.logger import get_logger
from ..cache import get_policy_cache, get_chat_cache
from ..vector_store import get_qdrant_manager
from ..db.engine import get_db
from ..db.models import Policy

logger = get_logger()
router = APIRouter()

# 캐시 인스턴스
policy_cache = get_policy_cache()
chat_cache = get_chat_cache()


# Request/Response models
class InitPolicyRequest(BaseModel):
    session_id: str
    policy_id: int


class InitPolicyResponse(BaseModel):
    session_id: str
    policy_id: int
    status: str
    message: str
    documents_count: int


class CleanupRequest(BaseModel):
    session_id: str


class CleanupResponse(BaseModel):
    session_id: str
    status: str
    message: str


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
    "/chat/init-policy",
    response_model=InitPolicyResponse,
    summary="공고 선택 시 문서 초기화",
    description="사용자가 공고를 클릭했을 때 해당 정책의 전체 문서를 캐시에 저장합니다.",
    tags=["Chat"]
)
async def init_policy(request: InitPolicyRequest):
    """
    공고 선택 시 문서 초기화 API
    
    **기능:**
    - 공고 선택 시 정책 문서 전체를 캐시에 저장
    - 이후 질문에서는 Qdrant 검색 없이 캐시 재사용 (100배 빠름!)
    
    **예시:**
    ```json
    {
      "session_id": "abc-123",
      "policy_id": 5
    }
    ```
    """
    try:
        session_id = request.session_id
        policy_id = request.policy_id
        
        # 1. DB에서 정책 정보 조회
        with get_db() as db:
            policy = db.query(Policy).filter(Policy.id == policy_id).first()
            
            if not policy:
                raise HTTPException(
                    status_code=404,
                    detail=f"정책 ID {policy_id}를 찾을 수 없습니다."
                )
            
            policy_info = {
                "name": policy.program_name,
                "overview": policy.program_overview or "",
                "apply_target": policy.apply_target or "",
                "support_description": policy.support_description or ""
            }
        
        # 2. Qdrant에서 해당 정책의 모든 문서 가져오기 (벡터 검색 아님!)
        qdrant_manager = get_qdrant_manager()
        documents = qdrant_manager.get_all_documents(
            filter_dict={"policy_id": policy_id}
        )
        
        # 3. 캐시에 저장
        policy_cache.set_policy_context(
            session_id=session_id,
            policy_id=policy_id,
            policy_info=policy_info,
            documents=documents
        )
        
        logger.info(
            "Policy initialized successfully",
            extra={
                "session_id": session_id,
                "policy_id": policy_id,
                "documents_count": len(documents)
            }
        )
        
        return InitPolicyResponse(
            session_id=session_id,
            policy_id=policy_id,
            status="initialized",
            message="정책 문서가 로드되었습니다.",
            documents_count=len(documents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error initializing policy",
            extra={
                "session_id": request.session_id,
                "policy_id": request.policy_id,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"정책 초기화 중 오류가 발생했습니다: {str(e)}"
        )


@router.post(
    "/chat/cleanup",
    response_model=CleanupResponse,
    summary="대화창 나갈 때 캐시 정리",
    description="사용자가 대화창을 나갈 때 캐시를 즉시 삭제합니다 (메모리 효율).",
    tags=["Chat"]
)
async def cleanup_session(request: CleanupRequest):
    """
    대화창 나갈 때 캐시 정리 API
    
    **기능:**
    - 대화 이력 캐시 삭제
    - 정책 문서 캐시 삭제
    - 메모리 효율적 관리
    
    **프론트엔드 연동:**
    - 컴포넌트 unmount 시 호출
    
    **예시:**
    ```json
    {
      "session_id": "abc-123"
    }
    ```
    """
    try:
        session_id = request.session_id
        
        # 대화 이력 캐시 삭제
        chat_cache.clear_session(session_id)
        
        # 정책 문서 캐시 삭제
        policy_cache.clear_policy_context(session_id)
        
        logger.info(
            "Session cleaned up successfully",
            extra={"session_id": session_id}
        )
        
        return CleanupResponse(
            session_id=session_id,
            status="cleaned",
            message="캐시가 정리되었습니다."
        )
        
    except Exception as e:
        logger.error(
            "Error cleaning up session",
            extra={"session_id": request.session_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"캐시 정리 중 오류가 발생했습니다: {str(e)}"
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
    - 캐시 정리 (대화 이력, 정책 문서)
    - DB 세션 삭제 (선택적)
    - 홈으로 돌아갈 때 호출
    
    **예시:**
    ```
    POST /session/reset?session_id=abc-123
    ```
    """
    try:
        # 캐시 정리
        chat_cache.clear_session(session_id)
        policy_cache.clear_policy_context(session_id)
        
        # DB 세션 삭제 (선택적 - 현재는 DB 사용 안 함)
        # success = AgentController.reset_session(session_id)
        
        logger.info(
            "Session reset successfully",
            extra={"session_id": session_id}
        )
        
        return SessionResetResponse(
            session_id=session_id,
            success=True,
            message="세션이 초기화되었습니다."
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

