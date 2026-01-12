"""
Policy Repository
정책 데이터 접근 계층 (Repository Pattern)
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from ..models import Policy, Document
from ...config.logger import get_logger

logger = get_logger()


class PolicyRepository:
    """
    정책 데이터 접근 계층
    
    Attributes:
        db: SQLAlchemy 세션
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
    
    def get_by_id(self, policy_id: int) -> Optional[Policy]:
        """
        ID로 정책 조회
        
        Args:
            policy_id: 정책 ID
        
        Returns:
            Optional[Policy]: 정책 객체 또는 None
        """
        try:
            return self.db.query(Policy).filter(Policy.id == policy_id).first()
        except Exception as e:
            logger.error(
                "Error getting policy by ID",
                extra={"policy_id": policy_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def get_by_program_id(self, program_id: int) -> Optional[Policy]:
        """
        Program ID로 정책 조회
        
        Args:
            program_id: 프로그램 ID (data.json의 program_id)
        
        Returns:
            Optional[Policy]: 정책 객체 또는 None
        """
        try:
            return self.db.query(Policy).filter(Policy.program_id == program_id).first()
        except Exception as e:
            logger.error(
                "Error getting policy by program ID",
                extra={"program_id": program_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def search(
        self,
        region: Optional[str] = None,
        category: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Policy]:
        """
        조건별 정책 검색
        
        Args:
            region: 지역 필터
            category: 카테고리 필터
            query: 검색 쿼리 (정책명, 개요에서 검색)
            limit: 반환 개수
            offset: 오프셋
        
        Returns:
            List[Policy]: 정책 리스트
        """
        try:
            q = self.db.query(Policy)
            
            # Apply filters
            if region:
                q = q.filter(Policy.region == region)
            
            if category:
                q = q.filter(Policy.category == category)
            
            if query:
                # Search in program_name or program_overview
                search_filter = or_(
                    Policy.program_name.like(f"%{query}%"),
                    Policy.program_overview.like(f"%{query}%")
                )
                q = q.filter(search_filter)
            
            # Order by created_at (newest first)
            q = q.order_by(Policy.created_at.desc())
            
            # Apply limit and offset
            return q.limit(limit).offset(offset).all()
            
        except Exception as e:
            logger.error(
                "Error searching policies",
                extra={
                    "region": region,
                    "category": category,
                    "query": query,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[Policy]:
        """
        모든 정책 조회
        
        Args:
            limit: 반환 개수
            offset: 오프셋
        
        Returns:
            List[Policy]: 정책 리스트
        """
        try:
            return self.db.query(Policy).order_by(Policy.created_at.desc()).limit(limit).offset(offset).all()
        except Exception as e:
            logger.error(
                "Error getting all policies",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def create(self, policy_data: dict) -> Policy:
        """
        정책 생성
        
        Args:
            policy_data: 정책 데이터
        
        Returns:
            Policy: 생성된 정책 객체
        """
        try:
            policy = Policy(**policy_data)
            self.db.add(policy)
            self.db.commit()
            self.db.refresh(policy)
            
            logger.info(
                "Policy created",
                extra={"policy_id": policy.id, "program_id": policy.program_id}
            )
            
            return policy
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error creating policy",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def update(self, policy_id: int, policy_data: dict) -> Optional[Policy]:
        """
        정책 업데이트
        
        Args:
            policy_id: 정책 ID
            policy_data: 업데이트할 데이터
        
        Returns:
            Optional[Policy]: 업데이트된 정책 객체 또는 None
        """
        try:
            policy = self.get_by_id(policy_id)
            if not policy:
                return None
            
            for key, value in policy_data.items():
                setattr(policy, key, value)
            
            self.db.commit()
            self.db.refresh(policy)
            
            logger.info(
                "Policy updated",
                extra={"policy_id": policy_id}
            )
            
            return policy
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error updating policy",
                extra={"policy_id": policy_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def delete(self, policy_id: int) -> bool:
        """
        정책 삭제
        
        Args:
            policy_id: 정책 ID
        
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            policy = self.get_by_id(policy_id)
            if not policy:
                return False
            
            self.db.delete(policy)
            self.db.commit()
            
            logger.info(
                "Policy deleted",
                extra={"policy_id": policy_id}
            )
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Error deleting policy",
                extra={"policy_id": policy_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def count(self, region: Optional[str] = None, category: Optional[str] = None) -> int:
        """
        정책 개수 조회
        
        Args:
            region: 지역 필터
            category: 카테고리 필터
        
        Returns:
            int: 정책 개수
        """
        try:
            q = self.db.query(Policy)
            
            if region:
                q = q.filter(Policy.region == region)
            
            if category:
                q = q.filter(Policy.category == category)
            
            return q.count()
            
        except Exception as e:
            logger.error(
                "Error counting policies",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def get_documents(self, policy_id: int) -> List[Document]:
        """
        특정 정책의 문서 조회
        
        Args:
            policy_id: 정책 ID
        
        Returns:
            List[Document]: 문서 리스트
        """
        try:
            return self.db.query(Document).filter(Document.policy_id == policy_id).all()
        except Exception as e:
            logger.error(
                "Error getting policy documents",
                extra={"policy_id": policy_id, "error": str(e)},
                exc_info=True
            )
            raise

