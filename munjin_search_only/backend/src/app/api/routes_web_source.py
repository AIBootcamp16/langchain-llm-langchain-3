"""
웹 근거 조회 API
웹 검색 결과의 상세 정보를 제공합니다.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config.logger import get_logger
from ..db.engine import get_db_session
from ..db.models import WebSource

logger = get_logger()
router = APIRouter(prefix="/api/v1", tags=["Web Sources"])


# ============================================================
# Pydantic Models
# ============================================================

class WebSourceResponse(BaseModel):
    """웹 근거 응답"""
    id: int = Field(..., description="웹 근거 ID")
    url: str = Field(..., description="원본 URL")
    title: str = Field(..., description="제목")
    snippet: Optional[str] = Field(None, description="요약 스니펫")
    content: Optional[str] = Field(None, description="전체 내용")
    source_type: str = Field(..., description="소스 타입 (tavily, duckduckgo)")
    fetched_date: Optional[str] = Field(None, description="조회일")
    created_at: str = Field(..., description="생성일")
    
    class Config:
        from_attributes = True


# ============================================================
# API Endpoints
# ============================================================

@router.get(
    "/web-source/{source_id}",
    response_model=WebSourceResponse,
    summary="웹 근거 조회",
    description="웹 검색 결과의 상세 정보를 조회합니다.",
)
async def get_web_source(
    source_id: int,
    db: Session = Depends(get_db_session)
):
    """
    웹 근거 상세 조회
    
    Args:
        source_id: 웹 근거 ID
        db: 데이터베이스 세션
        
    Returns:
        WebSourceResponse: 웹 근거 상세 정보
        
    Raises:
        HTTPException: 웹 근거를 찾을 수 없는 경우
    """
    try:
        # DB에서 웹 근거 조회
        web_source = db.query(WebSource).filter(WebSource.id == source_id).first()
        
        if not web_source:
            logger.warning(f"Web source not found: {source_id}")
            raise HTTPException(
                status_code=404,
                detail=f"웹 근거를 찾을 수 없습니다. (ID: {source_id})"
            )
        
        # 응답 생성
        return WebSourceResponse(
            id=web_source.id,
            url=web_source.url,
            title=web_source.title,
            snippet=web_source.snippet,
            content=web_source.content,
            source_type=web_source.source_type.value,
            fetched_date=web_source.fetched_date.isoformat() if web_source.fetched_date else None,
            created_at=web_source.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching web source {source_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="웹 근거를 조회하는 중 오류가 발생했습니다."
        )


@router.get(
    "/web-sources",
    response_model=list[WebSourceResponse],
    summary="웹 근거 목록 조회",
    description="세션 또는 정책별 웹 근거 목록을 조회합니다.",
)
async def list_web_sources(
    session_id: Optional[str] = None,
    policy_id: Optional[int] = None,
    limit: int = 10,
    db: Session = Depends(get_db_session)
):
    """
    웹 근거 목록 조회
    
    Args:
        session_id: 세션 ID (선택)
        policy_id: 정책 ID (선택)
        limit: 최대 조회 개수
        db: 데이터베이스 세션
        
    Returns:
        list[WebSourceResponse]: 웹 근거 목록
    """
    try:
        query = db.query(WebSource)
        
        # 필터 적용
        if session_id:
            query = query.filter(WebSource.session_id == session_id)
        if policy_id:
            query = query.filter(WebSource.policy_id == policy_id)
        
        # 최신순 정렬 및 제한
        web_sources = query.order_by(WebSource.created_at.desc()).limit(limit).all()
        
        # 응답 생성
        return [
            WebSourceResponse(
                id=ws.id,
                url=ws.url,
                title=ws.title,
                snippet=ws.snippet,
                content=ws.content,
                source_type=ws.source_type.value,
                fetched_date=ws.fetched_date.isoformat() if ws.fetched_date else None,
                created_at=ws.created_at.isoformat()
            )
            for ws in web_sources
        ]
        
    except Exception as e:
        logger.error(f"Error fetching web sources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="웹 근거 목록을 조회하는 중 오류가 발생했습니다."
        )

