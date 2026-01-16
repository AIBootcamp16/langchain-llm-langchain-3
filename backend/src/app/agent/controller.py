"""
Agent Controller
LangGraph 워크플로우 진입점
"""

from typing import Dict, Any, List, Optional
import uuid

from ..config.logger import get_logger
from ..cache import get_chat_cache
from ..observability import trace_workflow, get_feature_tags
from ..services.simple_search_service import get_simple_search_service
# DB 관련 import는 유지 (추후 필요 시 재사용 가능)
# from ..db.engine import get_db
# from ..db.repositories import SessionRepository
# from ..db.models import WorkflowTypeEnum, RoleEnum
from .workflows import run_qa_workflow

logger = get_logger()
chat_cache = get_chat_cache()


class AgentController:
    """
    에이전트 컨트롤러
    
    워크플로우 실행 및 세션 관리
    """
    
    @staticmethod
    @trace_workflow(
        name="agent_controller_run_qa",
        tags=None,  # 런타임에 동적으로 추가
        metadata={"controller": "qa", "version": "v2_cache"}
    )
    def run_qa(
        session_id: str,
        policy_id: int,
        user_message: str
    ) -> Dict[str, Any]:
        """
        Q&A 워크플로우 실행
        
        Args:
            session_id: 세션 ID
            policy_id: 정책 ID
            user_message: 사용자 메시지
        
        Returns:
            Dict: 실행 결과
        """
        try:
            # 캐시에서 대화 이력 조회 (DB 대신 메모리 캐시 사용)
            messages = chat_cache.get_chat_history(session_id)
            
            logger.info(
                "Running Q&A workflow",
                extra={
                    "session_id": session_id,
                    "policy_id": policy_id,
                    "history_messages": len(messages)
                }
            )
            
            # 사용자 메시지를 캐시에 추가
            chat_cache.add_message(
                    session_id=session_id,
                role="user",
                    content=user_message
                )
            
            # 워크플로우 실행
            result = run_qa_workflow(
                session_id=session_id,
                policy_id=policy_id,
                user_query=user_message,
                messages=messages
            )
            
            # 어시스턴트 응답을 캐시에 저장
            chat_cache.add_message(
                    session_id=session_id,
                role="assistant",
                content=result.get("answer", "")
            )
            
            logger.info(
                "Q&A workflow completed",
                extra={
                    "session_id": session_id,
                    "has_answer": bool(result.get("answer"))
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
    @trace_workflow(
        name="agent_controller_run_search",
        tags=None,
        metadata={"controller": "search", "version": "v2_simple"}
    )
    def run_search(
        query: str,
        session_id: Optional[str] = None,
        region: Optional[str] = None,
        category: Optional[str] = None,
        target_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        검색 실행 (SimpleSearchService 사용)
        
        Args:
            query: 검색 쿼리
            session_id: 세션 ID (없으면 자동 생성)
            region: 지역 필터
            category: 카테고리 필터
            target_group: 대상 그룹 필터
        
        Returns:
            Dict: 검색 결과
        """
        try:
            logger.info(
                "Running search workflow",
                extra={
                    "query": query,
                    "session_id": session_id,
                    "region": region,
                    "category": category
                }
            )
            
            # SimpleSearchService로 검색 실행
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
                "Search workflow completed",
                extra={
                    "session_id": result.get("session_id"),
                    "total_count": result.get("total_count"),
                    "is_sufficient": result.get("is_sufficient")
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Error in search controller",
                extra={
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
                "top_score": 0.0,
                "is_sufficient": False,
                "sufficiency_reason": f"오류: {str(e)}",
                "web_sources": [],
                "metrics": {},
                "evidence": [],
                "parsed_query": {
                    "intent": "policy_search",
                    "keywords": [],
                    "filters": {},
                    "sort_preference": "relevance",
                    "time_context": None
                },
                "error": str(e)
            }
    
    @staticmethod
    def reset_session(session_id: str) -> bool:
        """
        세션 초기화 (현재는 사용하지 않음 - API 레벨에서 직접 캐시 정리)
        
        Note: DB 저장을 하지 않으므로 이 메서드는 현재 사용하지 않습니다.
        캐시 정리는 routes_chat.py의 /session/reset 엔드포인트에서 직접 수행합니다.
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 성공 여부
        """
        try:
            # 캐시 정리 (API 레벨에서 직접 처리하므로 여기서는 생략)
            # chat_cache.clear_session(session_id)
            # policy_cache.clear_policy_context(session_id)
            
            # DB 저장을 하지 않으므로 DB 삭제도 불필요
            # with get_db() as db:
            #     session_repo = SessionRepository(db)
            #     return session_repo.delete(session_id)
            
            return True
            
        except Exception as e:
            logger.error(
                "Error resetting session",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            return False

