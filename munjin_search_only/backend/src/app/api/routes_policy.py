"""
Policy API Routes
정책 검색 및 조회 엔드포인트
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..db.engine import get_db_session
from ..services import PolicySearchService
from ..domain.policy import PolicyResponse, PolicyListResponse, PolicySearchRequest
from ..config.logger import get_logger
from ..agent.controller import AgentController

logger = get_logger()
router = APIRouter()


# =============================================================================
# Search Agent Response Models
# =============================================================================

class ParsedQueryResponse(BaseModel):
    """분석된 쿼리 정보"""
    intent: str = Field(default="policy_search", description="검색 의도")
    keywords: List[str] = Field(default_factory=list, description="추출된 키워드")
    filters: Dict[str, Any] = Field(default_factory=dict, description="필터 조건")
    sort_preference: str = Field(default="relevance", description="정렬 선호도")
    time_context: Optional[str] = Field(None, description="시간 컨텍스트")


class WebSourceResponse(BaseModel):
    """웹 검색 결과"""
    url: str = Field(..., description="URL")
    title: str = Field(..., description="제목")
    snippet: str = Field(..., description="요약")
    score: float = Field(default=0.0, description="점수")
    fetched_date: str = Field(..., description="조회일")
    source_type: str = Field(..., description="소스 타입 (tavily/duckduckgo)")


class SearchAgentPolicyResponse(BaseModel):
    """Search Agent 정책 응답"""
    id: int = Field(..., description="정책 ID")
    program_id: Optional[int] = Field(None, description="프로그램 ID")
    program_name: str = Field(..., description="정책명")
    program_overview: Optional[str] = Field(None, description="정책 개요")
    region: Optional[str] = Field(None, description="지역")
    category: Optional[str] = Field(None, description="카테고리")
    support_description: Optional[str] = Field(None, description="지원 내용")
    support_budget: Optional[int] = Field(None, description="지원 예산")
    apply_target: Optional[str] = Field(None, description="신청 대상")
    announcement_date: Optional[str] = Field(None, description="공고일")
    application_method: Optional[str] = Field(None, description="신청 방법")
    score: Optional[float] = Field(None, description="유사도 점수")
    source_type: str = Field(default="internal", description="소스 타입 (internal/web)")
    url: Optional[str] = Field(None, description="웹 소스 URL (웹 결과인 경우)")

    class Config:
        from_attributes = True


class SearchMetricsResponse(BaseModel):
    """검색 품질 지표"""
    total_candidates: int = Field(default=0, description="초기 후보 수")
    filtered_count: int = Field(default=0, description="필터링 후 결과 수")
    final_count: int = Field(default=0, description="최종 결과 수")
    top_score: float = Field(default=0.0, description="최고 유사도")
    avg_score: float = Field(default=0.0, description="평균 유사도")
    min_score: float = Field(default=0.0, description="최소 유사도")
    score_threshold_used: float = Field(default=0.0, description="사용된 유사도 임계값")
    web_search_triggered: bool = Field(default=False, description="웹 검색 수행 여부")
    web_search_count: int = Field(default=0, description="웹 검색 결과 수")
    search_time_ms: int = Field(default=0, description="검색 소요 시간 (ms)")
    sufficiency_reason: str = Field(default="", description="충분성 판단 사유")


class SearchEvidenceResponse(BaseModel):
    """검색 근거 정보"""
    policy_id: int = Field(..., description="정책 ID")
    matched_content: str = Field(..., description="매칭된 텍스트")
    score: float = Field(..., description="유사도 점수")
    match_type: str = Field(default="vector", description="매칭 타입")


class SearchAgentResponse(BaseModel):
    """Search Agent 응답 (SimpleSearchService 기반)"""
    session_id: str = Field(..., description="세션 ID")
    summary: str = Field(..., description="검색 결과 요약")
    policies: List[SearchAgentPolicyResponse] = Field(default_factory=list, description="정책 리스트")
    total_count: int = Field(..., description="전체 결과 수")
    parsed_query: ParsedQueryResponse = Field(..., description="분석된 쿼리 정보")
    top_score: float = Field(..., description="최고 유사도 점수")
    is_sufficient: bool = Field(..., description="검색 결과 충분 여부")
    sufficiency_reason: str = Field(..., description="충분성 판단 사유")
    web_sources: List[WebSourceResponse] = Field(default_factory=list, description="웹 검색 결과")
    metrics: Optional[SearchMetricsResponse] = Field(None, description="검색 품질 지표")
    evidence: List[SearchEvidenceResponse] = Field(default_factory=list, description="검색 근거")
    error: Optional[str] = Field(None, description="에러 메시지")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc-123",
                "summary": "'프리랜서 지원금' 검색 결과 5건을 찾았습니다.",
                "policies": [
                    {
                        "id": 1,
                        "program_name": "프리랜서 창업 지원 사업",
                        "region": "서울",
                        "category": "사업화",
                        "score": 0.85,
                        "source_type": "internal"
                    }
                ],
                "total_count": 5,
                "parsed_query": {
                    "intent": "condition_search",
                    "keywords": ["프리랜서", "지원금"],
                    "filters": {"target_group": "프리랜서"},
                    "sort_preference": "relevance"
                },
                "top_score": 0.85,
                "is_sufficient": True,
                "sufficiency_reason": "검색 결과 충분",
                "web_sources": [],
                "metrics": {
                    "total_candidates": 50,
                    "filtered_count": 10,
                    "final_count": 5,
                    "top_score": 0.85,
                    "avg_score": 0.65,
                    "search_time_ms": 150
                },
                "evidence": [
                    {
                        "policy_id": 1,
                        "matched_content": "프리랜서를 위한 창업 지원...",
                        "score": 0.85,
                        "match_type": "vector"
                    }
                ]
            }
        }


# =============================================================================
# Search Endpoint (빠른 벡터 검색 - LLM 호출 없음)
# =============================================================================

@router.get(
    "/policies/search",
    response_model=SearchAgentResponse,
    summary="정책 검색 (빠른 벡터 검색)",
    description="""
빠른 정책 검색 API (LLM 호출 없음)

**특징:**
- Dense 벡터 검색 (Qdrant)
- 동적 유사도 임계값 조정 (결과 수에 따라 자동 조절)
- 웹 검색 폴백 (Tavily) - 결과가 부족할 때만
- 검색 품질 지표 및 근거 제공

**유사도 설정:**
- 기본 임계값: 0.25 (낮은 값으로 더 많은 결과)
- 결과가 적으면 자동으로 임계값 낮춤
- 키워드별 가중치 적용 가능

**예시:**
- `/policies/search?query=프리랜서 지원금`
- `/policies/search?query=창업 지원&region=서울`
- `/policies/search?query=R&D&category=사업화`
""",
    tags=["Policies"]
)
async def search_policies_with_agent(
    query: str = Query(..., description="검색 쿼리 (필수)", min_length=1),
    session_id: Optional[str] = Query(None, description="세션 ID (선택, 미입력 시 자동 생성)"),
    region: Optional[str] = Query(None, description="지역 필터 (선택)"),
    category: Optional[str] = Query(None, description="카테고리 필터 (선택)"),
    target_group: Optional[str] = Query(None, description="대상 그룹 필터 (선택)")
):
    """
    빠른 정책 검색 API

    **검색 흐름:**
    1. 쿼리 키워드 추출 (규칙 기반)
    2. 동적 유사도 임계값 계산
    3. Qdrant 벡터 검색
    4. MySQL 메타데이터 필터링
    5. 결과 부족 시 웹 검색 보충 (Tavily)
    6. 검색 품질 지표 계산

    **충분성 기준:**
    - 결과 수 >= 2건
    - 최고 유사도 >= 0.35
    """
    try:
        logger.info(
            "Search request received",
            extra={
                "query": query,
                "session_id": session_id,
                "region": region,
                "category": category,
                "target_group": target_group
            }
        )

        # Run search via AgentController (uses SimpleSearchService)
        result = AgentController.run_search(
            query=query,
            session_id=session_id,
            region=region,
            category=category,
            target_group=target_group
        )

        # Convert to response model
        parsed_query = result.get("parsed_query", {})
        web_sources = result.get("web_sources", [])
        policies = result.get("policies", [])
        metrics = result.get("metrics", {})
        evidence = result.get("evidence", [])

        response = SearchAgentResponse(
            session_id=result.get("session_id", ""),
            summary=result.get("summary", ""),
            policies=[
                SearchAgentPolicyResponse(
                    id=p.get("id", 0),
                    program_id=p.get("program_id"),
                    program_name=p.get("program_name", ""),
                    program_overview=p.get("program_overview"),
                    region=p.get("region"),
                    category=p.get("category"),
                    support_description=p.get("support_description"),
                    support_budget=p.get("support_budget"),
                    apply_target=p.get("apply_target"),
                    announcement_date=p.get("announcement_date"),
                    application_method=p.get("application_method"),
                    score=p.get("score"),
                    source_type=p.get("source_type", "internal"),
                    url=p.get("url")
                )
                for p in policies
            ],
            total_count=result.get("total_count", 0),
            parsed_query=ParsedQueryResponse(
                intent=parsed_query.get("intent", "policy_search"),
                keywords=parsed_query.get("keywords", []),
                filters=parsed_query.get("filters", {}),
                sort_preference=parsed_query.get("sort_preference", "relevance"),
                time_context=parsed_query.get("time_context")
            ),
            top_score=result.get("top_score", 0.0),
            is_sufficient=result.get("is_sufficient", False),
            sufficiency_reason=result.get("sufficiency_reason", ""),
            web_sources=[
                WebSourceResponse(
                    url=ws.get("url", ""),
                    title=ws.get("title", ""),
                    snippet=ws.get("snippet", ""),
                    score=ws.get("score", 0.0),
                    fetched_date=ws.get("fetched_date", ""),
                    source_type=ws.get("source_type", "unknown")
                )
                for ws in web_sources
            ],
            metrics=SearchMetricsResponse(
                total_candidates=metrics.get("total_candidates", 0),
                filtered_count=metrics.get("filtered_count", 0),
                final_count=metrics.get("final_count", 0),
                top_score=metrics.get("top_score", 0.0),
                avg_score=metrics.get("avg_score", 0.0),
                min_score=metrics.get("min_score", 0.0),
                score_threshold_used=metrics.get("score_threshold_used", 0.0),
                web_search_triggered=metrics.get("web_search_triggered", False),
                web_search_count=metrics.get("web_search_count", 0),
                search_time_ms=metrics.get("search_time_ms", 0),
                sufficiency_reason=metrics.get("sufficiency_reason", "")
            ) if metrics else None,
            evidence=[
                SearchEvidenceResponse(
                    policy_id=e.get("policy_id", 0),
                    matched_content=e.get("matched_content", ""),
                    score=e.get("score", 0.0),
                    match_type=e.get("match_type", "vector")
                )
                for e in evidence
            ],
            error=result.get("error")
        )

        logger.info(
            "Search request completed",
            extra={
                "session_id": response.session_id,
                "total_count": response.total_count,
                "is_sufficient": response.is_sufficient,
                "search_time_ms": metrics.get("search_time_ms", 0)
            }
        )

        return response

    except Exception as e:
        logger.error(
            "Error in search endpoint",
            extra={"query": query, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


# =============================================================================
# Legacy Endpoints (기존 검색 API - 호환성 유지)
# =============================================================================


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

