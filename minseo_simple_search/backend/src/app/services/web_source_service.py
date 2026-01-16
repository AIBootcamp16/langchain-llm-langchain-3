"""
Web Source Service
웹 검색 결과 저장 및 관리 서비스
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from ..config.logger import get_logger
from ..db.models import WebSource
from ..observability import trace_db_operation

logger = get_logger()


class WebSourceService:
    """웹 검색 결과 저장 및 관리 서비스"""
    
    def __init__(self, db: Session):
        """
        Initialize service
        
        Args:
            db: Database session
        """
        self.db = db
    
    @trace_db_operation(name="save_web_sources", tags=["web_source", "save"])
    def save_web_sources(
        self,
        session_id: str,
        policy_id: int,
        query: str,
        sources: List[Dict[str, Any]]
    ) -> List[WebSource]:
        """
        웹 검색 결과를 DB에 저장
        
        Args:
            session_id: 세션 ID
            policy_id: 정책 ID
            query: 검색 쿼리
            sources: 웹 검색 결과 리스트
        
        Returns:
            List[WebSource]: 저장된 웹 소스 리스트
        """
        try:
            saved_sources = []
            
            for source in sources:
                web_source = WebSource(
                    session_id=session_id,
                    policy_id=policy_id,
                    query=query,
                    url=source.get("url", ""),
                    title=source.get("title", ""),
                    snippet=source.get("snippet", ""),
                    score=source.get("score"),
                    fetched_date=source.get("fetched_date"),
                    source_type=source.get("source_type", "unknown"),
                    created_at=datetime.utcnow()
                )
                
                self.db.add(web_source)
                saved_sources.append(web_source)
            
            self.db.commit()
            
            logger.info(
                "Web sources saved",
                extra={
                    "session_id": session_id,
                    "policy_id": policy_id,
                    "count": len(saved_sources)
                }
            )
            
            return saved_sources
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to save web sources",
                extra={
                    "session_id": session_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise
    
    @trace_db_operation(name="get_web_sources", tags=["web_source", "get"])
    def get_web_sources(
        self,
        session_id: Optional[str] = None,
        policy_id: Optional[int] = None,
        limit: int = 10
    ) -> List[WebSource]:
        """
        웹 검색 결과 조회
        
        Args:
            session_id: 세션 ID (선택)
            policy_id: 정책 ID (선택)
            limit: 최대 결과 수
        
        Returns:
            List[WebSource]: 웹 소스 리스트
        """
        try:
            query = self.db.query(WebSource)
            
            if session_id:
                query = query.filter(WebSource.session_id == session_id)
            
            if policy_id:
                query = query.filter(WebSource.policy_id == policy_id)
            
            sources = query.order_by(WebSource.created_at.desc()).limit(limit).all()
            
            logger.info(
                "Web sources retrieved",
                extra={
                    "session_id": session_id,
                    "policy_id": policy_id,
                    "count": len(sources)
                }
            )
            
            return sources
            
        except Exception as e:
            logger.error(
                "Failed to retrieve web sources",
                extra={"error": str(e)},
                exc_info=True
            )
            return []
    
    @trace_db_operation(name="delete_old_web_sources", tags=["web_source", "cleanup"])
    def delete_old_web_sources(self, days: int = 30) -> int:
        """
        오래된 웹 검색 결과 삭제
        
        Args:
            days: 삭제할 데이터의 기준 일수
        
        Returns:
            int: 삭제된 레코드 수
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted_count = self.db.query(WebSource).filter(
                WebSource.created_at < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(
                "Old web sources deleted",
                extra={
                    "days": days,
                    "deleted_count": deleted_count
                }
            )
            
            return deleted_count
            
        except Exception as e:
            self.db.rollback()
            logger.error(
                "Failed to delete old web sources",
                extra={"error": str(e)},
                exc_info=True
            )
            return 0

