"""
Policy API Routes
정책 검색 및 조회 API 라우터
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..db.engine import get_db
from ..services.policy_search_service import PolicySearchService
from ..domain.policy import PolicyResponse
from ..config.logger import get_logger
from ..agent.controller import AgentController

logger = get_logger()
router = APIRouter()

def get_db_session():
    """
    get_db가 contextmanager일 경우를 대비한 의존성 래퍼
    """
    with get_db() as db:
        yield db


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
    support_scale: Optional[str] = Field(None, description="지원 규모")
    supervising_ministry: Optional[str] = Field(None, description="주관 부처")
    apply_target: Optional[str] = Field(None, description="신청 대상")
    announcement_date: Optional[str] = Field(None, description="공고일")
    application_method: Optional[str] = Field(None, description="신청 방법")
    contact_agency: Optional[str] = Field(None, description="연락처 기관")
    created_at: Optional[str] = Field(None, description="생성일")
    score: Optional[float] = Field(None, description="유사도 점수")
    source_type: str = Field(default="internal", description="소스 타입 (internal/web)")
    url: Optional[str] = Field(None, description="웹 소스 URL (웹 결과인 경우)")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchAgentPolicyResponse":
        """리스트를 문자열로 변환하여 생성"""
        # contact_agency가 리스트인 경우 문자열로 변환
        contact_agency = data.get("contact_agency")
        if isinstance(contact_agency, list):
            contact_agency = ", ".join(str(item) for item in contact_agency) if contact_agency else None
        
        # application_method가 리스트인 경우 문자열로 변환
        application_method = data.get("application_method")
        if isinstance(application_method, list):
            application_method = ", ".join(str(item) for item in application_method) if application_method else None
        
        return cls(
            id=data.get("id", 0),
            program_id=data.get("program_id"),
            program_name=data.get("program_name", ""),
            program_overview=data.get("program_overview"),
            region=data.get("region"),
            category=data.get("category"),
            support_description=data.get("support_description"),
            support_budget=data.get("support_budget"),
            support_scale=data.get("support_scale"),
            supervising_ministry=data.get("supervising_ministry"),
            apply_target=data.get("apply_target"),
            announcement_date=data.get("announcement_date"),
            application_method=application_method,
            contact_agency=contact_agency,
            created_at=data.get("created_at"),
            score=data.get("score"),
            source_type=data.get("source_type", "internal"),
            url=data.get("url")
        )

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


# =============================================================================
# Search Endpoint (빠른 벡터 검색 - LLM 호출 없음)
# =============================================================================

@router.get(
    "/search",
    response_model=SearchAgentResponse,
    summary="정책 검색 (빠른 벡터 검색)",
    description="""
빠른 정책 검색 API (LLM 호출 없음)

**특징:**
- Dense 벡터 검색 (Qdrant)
- 하이브리드 검색 (Dense + Sparse BM25)
- 동적 유사도 임계값 조정 (결과 수에 따라 자동 조절)
- 웹 검색 폴백 (Tavily) - 결과가 부족할 때만
- 검색 품질 지표 및 근거 제공

**유사도 설정:**
- 기본 임계값: 0.25 (낮은 값으로 더 많은 결과)
- 결과가 적으면 자동으로 임계값 낮춤
- 키워드별 가중치 적용 가능

**예시:**
- `/api/v1/policies/search?query=프리랜서 지원금`
- `/api/v1/policies/search?query=창업 지원&region=서울`
- `/api/v1/policies/search?query=R&D&category=사업화`
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
    3. Qdrant 벡터 검색 (하이브리드: Dense + Sparse)
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
                SearchAgentPolicyResponse.from_dict(p)
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

@router.get("", summary="정책 검색 및 목록 조회")
def search_policies(
    # 프론트엔드는 query 파라미터를 사용하고, 백엔드 초기 버전은 q를 사용하므로 둘 다 지원합니다.
    q: Optional[str] = Query(
        None,
        description="검색어 (키워드, 구파라미터 - 프론트에서는 query 사용)",
    ),
    query: Optional[str] = Query(
        None,
        description="검색어 (키워드, 기본 파라미터)",
    ),
    region: Optional[str] = Query(None, description="지역 필터"),
    category: Optional[str] = Query(None, description="분야 필터"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(10, ge=1, le=100, description="페이지 당 항목 수"),
    db: Session = Depends(get_db_session),
):
    """
    정책 정보를 검색하거나 목록을 조회합니다.

    - 프론트엔드는 `query` 파라미터를 사용합니다.
    - 과거 클라이언트/테스트 코드에서 `q`를 사용할 수도 있으므로 둘 다 허용하고,
      실제 검색어는 q > query 순으로 결정합니다.
    """
    effective_query = q if q is not None else query

    service = PolicySearchService(db)
    offset = (page - 1) * limit

    # 서비스 계층의 하이브리드 검색 호출
    policies, total = service.hybrid_search(
        query=effective_query,
        region=region,
        category=category,
        limit=limit,
        offset=offset,
    )

    return {
        "items": policies,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/regions", summary="지역 목록 조회")
def get_regions(db: Session = Depends(get_db_session)):
    """
    정책에 등록된 모든 지역 목록을 조회합니다.
    """
    try:
        from ..db.models import Policy
        
        regions = db.query(Policy.region).filter(Policy.region.isnot(None)).distinct().all()
        region_list = [r[0] for r in regions if r[0]]
        
        return sorted(region_list)
    except Exception as e:
        logger.error("Error getting regions", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"지역 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/categories", summary="카테고리 목록 조회")
def get_categories(db: Session = Depends(get_db_session)):
    """
    정책에 등록된 모든 카테고리 목록을 조회합니다.
    """
    try:
        from ..db.models import Policy
        
        categories = db.query(Policy.category).filter(Policy.category.isnot(None)).distinct().all()
        category_list = [c[0] for c in categories if c[0]]
        
        return sorted(category_list)
    except Exception as e:
        logger.error("Error getting categories", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=500, detail=f"카테고리 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{policy_id}", response_model=PolicyResponse, summary="정책 상세 조회")
def get_policy_detail(policy_id: int, db: Session = Depends(get_db_session)):
    service = PolicySearchService(db)
    policy = service.get_by_id(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="해당 정책을 찾을 수 없습니다.")
    return policy