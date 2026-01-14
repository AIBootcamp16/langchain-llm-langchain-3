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


class SearchAgentResponse(BaseModel):
    """Search Agent 응답"""
    session_id: str = Field(..., description="세션 ID")
    summary: str = Field(..., description="검색 결과 요약")
    policies: List[SearchAgentPolicyResponse] = Field(default_factory=list, description="정책 리스트")
    total_count: int = Field(..., description="전체 결과 수")
    parsed_query: ParsedQueryResponse = Field(..., description="분석된 쿼리 정보")
    top_score: float = Field(..., description="최고 유사도 점수")
    is_sufficient: bool = Field(..., description="검색 결과 충분 여부")
    sufficiency_reason: str = Field(..., description="충분성 판단 사유")
    web_sources: List[WebSourceResponse] = Field(default_factory=list, description="웹 검색 결과")
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
                "web_sources": []
            }
        }


# =============================================================================
# Search Agent Endpoint (LangGraph 기반 고도화된 검색)
# =============================================================================

@router.get(
    "/policies/search",
    response_model=SearchAgentResponse,
    summary="[Agent] 정책 검색 (LangGraph)",
    description="""
LangGraph 기반 고도화된 정책 검색 API

**워크플로우:**
1. Query Understanding (LLM): 쿼리 분석 → 의도, 키워드, 필터 추출
2. Retrieve (Qdrant + MySQL): 하이브리드 벡터 검색
3. Check Sufficiency: top_1 유사도 >= 0.65 검사
4. [조건부] Web Search (Tavily): 불충분 시 웹 검색 보충
5. Summarize (LLM): 결과 요약 및 정책 리스트 구성

**특징:**
- "최신" 키워드 → created_at DESC 정렬
- "프리랜서" 등 대상 그룹 → 자동 필터 적용
- 유사도 0.65 미만 시 웹 검색으로 보충

**예시:**
- `/policies/search?query=프리랜서 지원금`
- `/policies/search?query=최신 청년 창업 지원`
- `/policies/search?query=서울 중소기업 R&D`
""",
    tags=["Policies", "Agent"]
)
async def search_policies_with_agent(
    query: str = Query(..., description="검색 쿼리 (필수)", min_length=1),
    session_id: Optional[str] = Query(None, description="세션 ID (선택, 미입력 시 자동 생성)")
):
    """
    LangGraph 기반 고도화된 정책 검색 API

    **워크플로우 흐름:**
    START → query_understanding → retrieve → check_sufficiency
                                                    ↓
              summarize ← [충분] | [부족] → web_search → summarize → END

    **충분성 기준:**
    - top_1 유사도 >= 0.65
    - 결과 수 >= 2개
    """
    try:
        logger.info(
            "Search agent request received",
            extra={"query": query, "session_id": session_id}
        )

        # Run search workflow via AgentController
        result = AgentController.run_search(
            query=query,
            session_id=session_id
        )

        # Convert to response model
        parsed_query = result.get("parsed_query", {})
        web_sources = result.get("web_sources", [])
        policies = result.get("policies", [])

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
            error=result.get("error")
        )

        logger.info(
            "Search agent request completed",
            extra={
                "session_id": response.session_id,
                "total_count": response.total_count,
                "is_sufficient": response.is_sufficient
            }
        )

        return response

    except Exception as e:
        logger.error(
            "Error in search agent endpoint",
            extra={"query": query, "error": str(e)},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"검색 에이전트 실행 중 오류가 발생했습니다: {str(e)}"
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

