"""
Agent Controller
LangGraph 워크플로우 진입점

Note: Search Agent 워크플로우는 SimpleSearchService로 대체되었습니다.
      (성능 최적화: LLM 호출 제거, 빠른 벡터 검색)
"""

from typing import Dict, Any, List, Optional
import uuid

from ..config.logger import get_logger
from ..db.engine import get_db
from ..db.repositories import SessionRepository
from ..db.models import WorkflowTypeEnum, RoleEnum
from ..domain.policy import PolicyResponse
from .workflows import run_qa_workflow
# NOTE: create_search_workflow는 더 이상 사용하지 않음 (SimpleSearchService로 대체)
# from .workflows.search_workflow import create_search_workflow

logger = get_logger()


class AgentController:
    """
    에이전트 컨트롤러
    
    워크플로우 실행 및 세션 관리
    """
    
    # NOTE: _search_app과 구버전 run_search는 더 이상 사용하지 않음 (SimpleSearchService로 대체)
    # _search_app = create_search_workflow()

    @staticmethod
    def run_qa(
        session_id: str,
        policy_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Q&A 워크플로우 실행
        
        Args:
            session_id: 세션 ID (없으면 새로 생성)
            policy_id: 정책 ID
            user_message: 사용자 메시지
        
        Returns:
            Dict: 실행 결과
        """
        try:
            # Get or create session
            with get_db() as db:
                session_repo = SessionRepository(db)
                
                # Check if session exists
                session = session_repo.get_by_id(session_id)
                
                if not session:
                    # Create new session
                    logger.info(
                        "Creating new Q&A session",
                        extra={"session_id": session_id, "policy_id": policy_id}
                    )
                    session = session_repo.create(
                        session_id=session_id,
                        workflow_type=WorkflowTypeEnum.QA,
                        policy_id=policy_id
                    )
                
                # Get chat history
                messages = []
                chat_history = session_repo.get_chat_history(session_id, limit=10)
                for chat in chat_history:
                    messages.append({
                        "role": chat.role.value,
                        "content": chat.content
                    })
                
                # Add user message to history
                session_repo.add_chat_message(
                    session_id=session_id,
                    role=RoleEnum.USER,
                    content=user_message
                )
            
            # Run workflow
            result = run_qa_workflow(
                session_id=session_id,
                policy_id=policy_id,
                user_query=user_message,
                messages=messages
            )
            
            # Save assistant response
            with get_db() as db:
                session_repo = SessionRepository(db)
                session_repo.add_chat_message(
                    session_id=session_id,
                    role=RoleEnum.ASSISTANT,
                    content=result.get("answer", ""),
                    metadata={
                        "evidence": result.get("evidence", []),
                        "retrieved_docs_count": len(result.get("retrieved_docs", [])),
                        "web_sources_count": len(result.get("web_sources", []))
                    }
                )
            
            return {
                "session_id": session_id,
                "policy_id": policy_id,
                "answer": result.get("answer", ""),
                "evidence": result.get("evidence", []),
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(
                "Error in Q&A controller",
                extra={
                    "session_id": session_id,
                    "policy_id": policy_id,
                    "error": str(e)
                },
                exc_info=True
            )
            return {
                "session_id": session_id,
                "policy_id": policy_id,
                "answer": f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}",
                "evidence": [],
                "error": str(e)
            }
    
    @staticmethod
    def reset_session(session_id: str) -> bool:
        """
        세션 초기화
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            with get_db() as db:
                session_repo = SessionRepository(db)
                return session_repo.delete(session_id)
        except Exception as e:
            logger.error(
                "Error resetting session",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            return False

    @staticmethod
    def run_search(
        query: str,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
        category: Optional[str] = None,
        target_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        간소화된 정책 검색 실행 (SimpleSearchService 사용)

        기존 LangGraph 워크플로우 대신 빠른 벡터 검색을 수행합니다.
        - LLM 호출 없이 빠른 검색
        - 동적 유사도 임계값 조정
        - 웹 검색 폴백 (Tavily)
        - 검색 품질 지표 및 근거 제공

        Args:
            query: 검색 쿼리
            session_id: 세션 ID (선택, 없으면 자동 생성)
            region: 지역 필터 (선택)
            category: 카테고리 필터 (선택)
            target_group: 대상 그룹 필터 (선택)

        Returns:
            Dict: 검색 결과
                - session_id: 세션 ID
                - summary: 검색 결과 요약
                - policies: 정책 리스트
                - total_count: 전체 결과 수
                - parsed_query: 분석된 쿼리 정보
                - top_score: 최고 유사도 점수
                - is_sufficient: 충분성 여부
                - sufficiency_reason: 충분성 판단 사유
                - web_sources: 웹 검색 결과 (불충분 시)
                - metrics: 검색 품질 지표
                - evidence: 검색 근거 리스트
                - error: 에러 메시지 (선택)
        """
        try:
            # 지연 import로 순환 import 방지
            from ..services import get_simple_search_service
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            logger.info(
                "Starting simple search",
                extra={
                    "session_id": session_id,
                    "query": query,
                    "region": region,
                    "category": category,
                    "target_group": target_group
                }
            )

            # Use SimpleSearchService instead of LangGraph workflow
            search_service = get_simple_search_service()
            result = search_service.search(
                query=query,
                region=region,
                category=category,
                target_group=target_group,
                session_id=session_id,
                include_web_search=True
            )

            logger.info(
                "Simple search completed",
                extra={
                    "session_id": session_id,
                    "total_count": result.get("total_count", 0),
                    "is_sufficient": result.get("is_sufficient", False),
                    "search_time_ms": result.get("metrics", {}).get("search_time_ms", 0)
                }
            )

            return result

        except Exception as e:
            logger.error(
                "Error in search controller",
                extra={
                    "session_id": session_id,
                    "query": query,
                    "error": str(e)
                },
                exc_info=True
            )
            return {
                "session_id": session_id or str(uuid.uuid4()),
                "original_query": query,
                "summary": f"검색 중 오류가 발생했습니다: {str(e)}",
                "policies": [],
                "total_count": 0,
                "parsed_query": {},
                "top_score": 0.0,
                "is_sufficient": False,
                "sufficiency_reason": f"오류: {str(e)}",
                "web_sources": [],
                "metrics": {},
                "evidence": [],
                "error": str(e)
            }
