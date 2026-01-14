"""
Session Repository
세션 데이터 접근 계층
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session as SASession

from ..models import Session, Slot, ChatHistory, ChecklistResult, WorkflowTypeEnum, RoleEnum
from ...config.logger import get_logger

logger = get_logger()


class SessionRepository:
    """
    세션 데이터 접근 계층
    
    Attributes:
        db: SQLAlchemy 세션
    """
    
    def __init__(self, db: SASession):
        """
        Initialize repository
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, session_id: str) -> Optional[Session]:
        """
        ID로 세션 조회
        
        Args:
            session_id: 세션 ID (UUID)
        
        Returns:
            Optional[Session]: 세션 객체 또는 None
        """
        try:
            return self.db.query(Session).filter(Session.id == session_id).first()
        except Exception as e:
            logger.error(
                "Error getting session by ID",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def create(
        self,
        session_id: str,
        workflow_type: WorkflowTypeEnum,
        policy_id: Optional[int] = None,
        user_id: Optional[str] = None,
        state: Optional[dict] = None
    ) -> Session:
        """
        세션 생성
        
        Args:
            session_id: 세션 ID (UUID)
            workflow_type: 워크플로우 타입
            policy_id: 정책 ID (선택)
            user_id: 사용자 ID (선택)
            state: 세션 상태 (선택)
        
        Returns:
            Session: 생성된 세션 객체
        """
        try:
            session = Session(
                id=session_id,
                workflow_type=workflow_type,
                policy_id=policy_id,
                user_id=user_id,
                state=state or {}
            )
            
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)
            
            logger.info(
                "Session created",
                extra={
                    "session_id": session_id,
                    "workflow_type": workflow_type,
                    "policy_id": policy_id
                }
            )
            
            return session
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error creating session",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def update_state(self, session_id: str, state: dict) -> Optional[Session]:
        """
        세션 상태 업데이트
        
        Args:
            session_id: 세션 ID
            state: 새로운 상태
        
        Returns:
            Optional[Session]: 업데이트된 세션 또는 None
        """
        try:
            session = self.get_by_id(session_id)
            if not session:
                return None
            
            session.state = state
            session.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(session)
            
            return session
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error updating session state",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def delete(self, session_id: str) -> bool:
        """
        세션 삭제
        
        Args:
            session_id: 세션 ID
        
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            session = self.get_by_id(session_id)
            if not session:
                return False
            
            self.db.delete(session)
            self.db.commit()
            
            logger.info("Session deleted", extra={"session_id": session_id})
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error deleting session",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    # ============================================================
    # Slot Operations
    # ============================================================
    
    def get_slots(self, session_id: str) -> List[Slot]:
        """
        세션의 모든 슬롯 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            List[Slot]: 슬롯 리스트
        """
        try:
            return self.db.query(Slot).filter(Slot.session_id == session_id).all()
        except Exception as e:
            logger.error(
                "Error getting slots",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def get_slot(self, session_id: str, slot_name: str) -> Optional[Slot]:
        """
        특정 슬롯 조회
        
        Args:
            session_id: 세션 ID
            slot_name: 슬롯 이름
        
        Returns:
            Optional[Slot]: 슬롯 객체 또는 None
        """
        try:
            return self.db.query(Slot).filter(
                Slot.session_id == session_id,
                Slot.slot_name == slot_name
            ).first()
        except Exception as e:
            logger.error(
                "Error getting slot",
                extra={"session_id": session_id, "slot_name": slot_name, "error": str(e)},
                exc_info=True
            )
            raise
    
    def set_slot(self, session_id: str, slot_name: str, slot_value: str) -> Slot:
        """
        슬롯 설정 (생성 또는 업데이트)
        
        Args:
            session_id: 세션 ID
            slot_name: 슬롯 이름
            slot_value: 슬롯 값
        
        Returns:
            Slot: 슬롯 객체
        """
        try:
            slot = self.get_slot(session_id, slot_name)
            
            if slot:
                # Update existing slot
                slot.slot_value = slot_value
            else:
                # Create new slot
                slot = Slot(
                    session_id=session_id,
                    slot_name=slot_name,
                    slot_value=slot_value
                )
                self.db.add(slot)
            
            self.db.commit()
            self.db.refresh(slot)
            
            return slot
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error setting slot",
                extra={"session_id": session_id, "slot_name": slot_name, "error": str(e)},
                exc_info=True
            )
            raise
    
    # ============================================================
    # Chat History Operations
    # ============================================================
    
    def get_chat_history(self, session_id: str, limit: int = 50) -> List[ChatHistory]:
        """
        채팅 이력 조회
        
        Args:
            session_id: 세션 ID
            limit: 반환 개수
        
        Returns:
            List[ChatHistory]: 채팅 이력 리스트
        """
        try:
            return self.db.query(ChatHistory).filter(
                ChatHistory.session_id == session_id
            ).order_by(ChatHistory.created_at.asc()).limit(limit).all()
        except Exception as e:
            logger.error(
                "Error getting chat history",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def add_chat_message(
        self,
        session_id: str,
        role: RoleEnum,
        content: str,
        metadata: Optional[dict] = None
    ) -> ChatHistory:
        """
        채팅 메시지 추가
        
        Args:
            session_id: 세션 ID
            role: 역할 (user, assistant, system)
            content: 메시지 내용
            metadata: 메타데이터 (선택)
        
        Returns:
            ChatHistory: 채팅 이력 객체
        """
        try:
            chat = ChatHistory(
                session_id=session_id,
                role=role,
                content=content,
                metadata=metadata or {}
            )
            
            self.db.add(chat)
            self.db.commit()
            self.db.refresh(chat)
            
            return chat
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error adding chat message",
                extra={"session_id": session_id, "role": role, "error": str(e)},
                exc_info=True
            )
            raise
    
    # ============================================================
    # Checklist Results Operations
    # ============================================================
    
    def get_checklist_results(self, session_id: str) -> List[ChecklistResult]:
        """
        체크리스트 결과 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            List[ChecklistResult]: 체크리스트 결과 리스트
        """
        try:
            return self.db.query(ChecklistResult).filter(
                ChecklistResult.session_id == session_id
            ).all()
        except Exception as e:
            logger.error(
                "Error getting checklist results",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def add_checklist_result(
        self,
        session_id: str,
        policy_id: int,
        condition_name: str,
        result: str,
        condition_value: Optional[str] = None,
        user_value: Optional[str] = None,
        reason: Optional[str] = None
    ) -> ChecklistResult:
        """
        체크리스트 결과 추가
        
        Args:
            session_id: 세션 ID
            policy_id: 정책 ID
            condition_name: 조건명
            result: 판정 결과 (PASS, FAIL, UNKNOWN)
            condition_value: 조건 값 (선택)
            user_value: 사용자 값 (선택)
            reason: 판정 사유 (선택)
        
        Returns:
            ChecklistResult: 체크리스트 결과 객체
        """
        try:
            checklist_result = ChecklistResult(
                session_id=session_id,
                policy_id=policy_id,
                condition_name=condition_name,
                condition_value=condition_value,
                user_value=user_value,
                result=result,
                reason=reason
            )
            
            self.db.add(checklist_result)
            self.db.commit()
            self.db.refresh(checklist_result)
            
            return checklist_result
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error adding checklist result",
                extra={"session_id": session_id, "error": str(e)},
                exc_info=True
            )
            raise

