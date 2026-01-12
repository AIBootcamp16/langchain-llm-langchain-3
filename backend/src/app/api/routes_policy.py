"""
Policy API Routes
정책 검색 및 조회 엔드포인트
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..db.engine import get_db_session
from ..services import PolicySearchService
from ..domain.policy import PolicyResponse, PolicyListResponse, PolicySearchRequest
from ..config.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.get(
    "/policies",
    response_model=PolicyListResponse,
    summary="정책 검색",
    description="키워드, 지역, 카테고리로 정책을 검색합니다. 쿼리가 있으면 벡터 검색, 없으면 필터링 검색을 수행합니다.",
    tags=["Policies"]
)
async def search_policies(
    query: Optional[str] = Query(None, description="검색 쿼리"),
    region: Optional[str] = Query(None, description="지역 필터"),
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(10, ge=1, le=100, description="반환 개수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    db: Session = Depends(get_db_session)
):
    """
    정책 검색 API
    
    **검색 방식:**
    - query가 있는 경우: Qdrant 벡터 검색 + MySQL 메타 필터링 (하이브리드 검색)
    - query가 없는 경우: MySQL 직접 조회 (필터링 검색)
    
    **필터:**
    - region: 지역 (예: "서울", "전국")
    - category: 카테고리 (예: "사업화", "글로벌")
    
    **예시:**
    - `/policies?query=창업+지원금&region=서울&limit=10`
    - `/policies?region=전국&category=사업화`
    """
    try:
        search_service = PolicySearchService(db)
        
        policies, total = search_service.hybrid_search(
            query=query,
            region=region,
            category=category,
            limit=limit,
            offset=offset
        )
        
        return PolicyListResponse(
            total=total,
            count=len(policies),
            offset=offset,
            limit=limit,
            policies=policies
        )
        
    except Exception as e:
        logger.error(
            "Error searching policies",
            extra={"error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"정책 검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/policy/{policy_id}",
    response_model=PolicyResponse,
    summary="정책 상세 조회",
    description="정책 ID로 특정 정책의 상세 정보를 조회합니다.",
    tags=["Policies"]
)
async def get_policy(
    policy_id: int,
    db: Session = Depends(get_db_session)
):
    """
    정책 상세 조회 API
    
    **응답:**
    - 정책의 모든 상세 정보 (신청 대상, 지원 내용, 일정, 연락처 등)
    
    **예시:**
    - `/policy/1`
    """
    try:
        search_service = PolicySearchService(db)
        policy = search_service.get_by_id(policy_id)
        
        if not policy:
            raise HTTPException(
                status_code=404,
                detail=f"정책 ID {policy_id}를 찾을 수 없습니다."
            )
        
        return policy
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting policy",
            extra={"policy_id": policy_id, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"정책 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get(
    "/policies/regions",
    response_model=list[str],
    summary="지역 목록 조회",
    description="사용 가능한 지역 목록을 조회합니다.",
    tags=["Policies"]
)
async def get_regions(db: Session = Depends(get_db_session)):
    """
    지역 목록 조회 API
    
    **응답:**
    - 정책 데이터에 있는 모든 지역 리스트
    """
    try:
        # Query distinct regions
        from ..db.models import Policy
        regions = db.query(Policy.region).distinct().filter(Policy.region.isnot(None)).all()
        return [r[0] for r in regions]
        
    except Exception as e:
        logger.error("Error getting regions", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/policies/categories",
    response_model=list[str],
    summary="카테고리 목록 조회",
    description="사용 가능한 카테고리 목록을 조회합니다.",
    tags=["Policies"]
)
async def get_categories(db: Session = Depends(get_db_session)):
    """
    카테고리 목록 조회 API
    
    **응답:**
    - 정책 데이터에 있는 모든 카테고리 리스트
    """
    try:
        # Query distinct categories
        from ..db.models import Policy
        categories = db.query(Policy.category).distinct().filter(Policy.category.isnot(None)).all()
        return [c[0] for c in categories]
        
    except Exception as e:
        logger.error("Error getting categories", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

