"""
Agent Controller
LangGraph 워크플로우 진입점
"""

from typing import Dict, Any, List
import uuid

from ..config.logger import get_logger
from ..db.engine import get_db
from ..db.repositories import SessionRepository
from ..db.models import WorkflowTypeEnum, RoleEnum
from .workflows import run_qa_workflow

logger = get_logger()


class AgentController:
    """
    에이전트 컨트롤러
    
    워크플로우 실행 및 세션 관리
    """
    
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

