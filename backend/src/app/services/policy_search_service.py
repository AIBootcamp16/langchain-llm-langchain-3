"""
Policy Search Service
정책 검색 비즈니스 로직 (Hybrid Search: Qdrant + MySQL + Web Search)
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..db.models import Policy
from ..db.repositories import PolicyRepository
from ..vector_store import get_qdrant_manager, get_embedder
from ..domain.policy import PolicyResponse
from ..config.logger import get_logger
from ..observability import trace_workflow, get_feature_tags
from ..web_search.clients import TavilySearchClient
# NOTE: create_search_workflow는 더 이상 사용하지 않음 (SimpleSearchService로 대체)

logger = get_logger()


class PolicySearchService:
    """
    정책 검색 서비스
    
    Attributes:
        db: SQLAlchemy 세션
        policy_repo: 정책 Repository
        qdrant_manager: Qdrant 관리자
        embedder: 임베딩 생성기
    """
    
    def __init__(self, db: Session):
        """
        Initialize service
        
        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.policy_repo = PolicyRepository(db)
        # NOTE:
        #   기존 버전에서는 검색 시 LangGraph 기반 Search Workflow + Qdrant 벡터 검색 + 웹 검색(Tavily)을
        #   함께 사용했습니다.
        #   현재 요구사항은 "에이전트/LLM 없이, 우리가 정리한 정책 DB 기준으로 바로 검색 결과를 주는 것"이므로
        #   검색 API에서는 아래 리포지토리 기반 검색만 사용합니다.
        #
        #   Qdrant/임베딩은 다른 기능(예: QA)에서 재사용할 수 있도록 초기화는 유지합니다.
        self.qdrant_manager = get_qdrant_manager()
        self.embedder = get_embedder()
        self.tavily_client = TavilySearchClient()
    
    @trace_workflow(
        name="hybrid_search",
        tags=get_feature_tags("PS"),
        run_type="chain"
    )
    def hybrid_search(
        self,
        query: Optional[str] = None,
        region: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        score_threshold: float = 0.2,
        min_results_for_web_search: int = 3
    ) -> tuple[List[PolicyResponse], int]:
        """
        하이브리드 검색 (Qdrant 벡터 검색 + MySQL 메타 필터링 + 웹 검색)
        
        Args:
            query: 검색 쿼리
            region: 지역 필터
            category: 카테고리 필터
            limit: 반환 개수
            offset: 오프셋
            score_threshold: 최소 스코어
            min_results_for_web_search: 웹 검색 트리거 최소 결과 수
        
        Returns:
            tuple: (정책 리스트, 전체 개수)
        """
        try:
            # ------------------------------------------------------------------
            # 단순 DB 기반 검색 (Agent/LLM 미사용)
            # ------------------------------------------------------------------
            #
            # 요구사항:
            #   - LangGraph / LLM 에이전트 없이, 우리가 정리한 정책 DB 기준으로 바로 검색 결과 제공
            #   - "창업"처럼 넓은 키워드는 많이 매칭되도록 최대한 너그럽게 검색
            #
            # 구현:
            #   - PolicyRepository.search 에서 program_name / program_overview 에 대해
            #     LIKE 검색을 수행 (query가 없으면 전체 목록)
            #   - region / category 는 그대로 필터링
            # ------------------------------------------------------------------

            logger.info(
                "Performing repository-based policy search",
                extra={
                    "query": query,
                    "region": region,
                    "category": category,
                    "limit": limit,
                    "offset": offset,
                },
            )

            # 1) 내부 DB 검색
            policies = self.policy_repo.search(
                region=region,
                category=category,
                query=query,
                limit=limit,
                offset=offset,
            )

            # Policy ORM 객체를 PolicyResponse로 변환
            policy_responses = [
                self._to_response(policy, score=getattr(policy, "score", None))
                for policy in policies
            ]
            
            # count도 query 파라미터를 포함해야 정확한 total을 계산할 수 있습니다
            # 하지만 PolicyRepository.count는 query를 지원하지 않으므로,
            # 검색 결과가 있을 때는 그 개수를 사용하고, 없을 때만 count를 사용합니다
            if query:
                # query가 있으면 검색 결과 개수를 total로 사용 (웹 검색 결과 포함 전)
                total = len(policy_responses)
            else:
                # query가 없으면 필터만 적용한 전체 개수
                total = self.policy_repo.count(region=region, category=category)

            # 2) 결과가 너무 적고 쿼리가 있을 때 웹 검색으로 보완
            web_results: List[PolicyResponse] = []
            if query and len(policy_responses) < min_results_for_web_search:
                try:
                    web_results = self._web_search(
                        query=query,
                        max_results=min_results_for_web_search - len(policy_responses),
                    )
                    # 내부 DB 결과 뒤에 웹 검색 결과를 이어붙임
                    policy_responses.extend(web_results)
                    total = len(policy_responses)
                except Exception as e:
                    # 웹 검색 실패해도 DB 결과는 반환
                    logger.warning(
                        "Web search failed, returning DB results only",
                        extra={"error": str(e), "db_results_count": len(policy_responses)}
                    )

            logger.info(
                "Search completed (DB + optional web search)",
                extra={
                    "query": query,
                    "db_results_count": len(policy_responses),
                    "web_results_count": len(web_results),
                    "total_returned": len(policy_responses),
                },
            )

            return policy_responses, total
            
        except Exception as e:
            logger.error(
                "Error in hybrid search",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _web_search(
        self,
        query: str,
        max_results: int = 5
    ) -> List[PolicyResponse]:
        """
        웹 검색 수행 (Tavily API 사용)
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
        
        Returns:
            List[PolicyResponse]: 웹 검색 결과를 PolicyResponse 형식으로 변환
        """
        try:
            # Tavily 웹 검색 실행
            web_results = self.tavily_client.search(
                query=f"{query} 정부 지원 사업 공고",
                max_results=max_results,
                search_depth="advanced"
            )
            
            if not web_results:
                logger.warning("No web search results found")
                return []
            
            # 웹 검색 결과를 PolicyResponse 형식으로 변환
            policy_responses = []
            for idx, result in enumerate(web_results):
                # 웹 검색 결과는 실제 정책이 아니므로 특별한 형식으로 변환
                policy_response = PolicyResponse(
                    id=-1000 - idx,  # 음수 ID로 웹 검색 결과 표시
                    program_id=-1,
                    region="웹 검색",
                    category="웹 검색 결과",
                    program_name=result.get("title", "제목 없음"),
                    program_overview=result.get("content", ""),
                    support_description=f"출처: {result.get('url', '')}",
                    support_budget=0,
                    support_scale="웹 검색",
                    supervising_ministry="웹 검색",
                    apply_target="웹 검색 결과 - 자세한 내용은 출처 링크를 확인하세요",
                    announcement_date=datetime.now().strftime("%Y-%m-%d"),
                    biz_process="",
                    application_method=f"자세한 내용은 다음 링크를 참고하세요: {result.get('url', '')}",
                    contact_agency=[result.get("url", "")],
                    contact_number=[],
                    required_documents=[],
                    collected_date=datetime.now().strftime("%Y-%m-%d"),
                    created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    score=result.get("score", 0.5)
                )
                policy_responses.append(policy_response)
            
            logger.info(
                "Web search results converted",
                extra={"count": len(policy_responses)}
            )
            
            return policy_responses
            
        except Exception as e:
            logger.error(
                "Error in web search",
                extra={"error": str(e)},
                exc_info=True
            )
            return []
    
    def get_by_id(self, policy_id: int) -> Optional[PolicyResponse]:
        """
        ID로 정책 조회
        
        Args:
            policy_id: 정책 ID
        
        Returns:
            Optional[PolicyResponse]: 정책 응답 또는 None
        """
        try:
            policy = self.policy_repo.get_by_id(policy_id)
            
            if not policy:
                logger.warning(
                    "Policy not found",
                    extra={"policy_id": policy_id}
                )
                return None
            
            return self._to_response(policy)
            
        except Exception as e:
            logger.error(
                "Error getting policy by ID",
                extra={"policy_id": policy_id, "error": str(e)},
                exc_info=True
            )
            raise
    
    def _to_response(self, policy: Policy, score: Optional[float] = None) -> PolicyResponse:
        """
        Policy 모델을 PolicyResponse로 변환
        
        Args:
            policy: Policy ORM 모델
            score: 검색 스코어 (선택)
        
        Returns:
            PolicyResponse: 정책 응답 모델
        """
        # contact_agency를 list로 변환 (string이면 list로)
        contact_agency = policy.contact_agency
        if contact_agency and isinstance(contact_agency, str):
            contact_agency = [contact_agency]
        
        return PolicyResponse(
            id=policy.id,
            program_id=policy.program_id,
            region=policy.region,
            category=policy.category,
            program_name=policy.program_name,
            program_overview=policy.program_overview,
            support_description=policy.support_description,
            support_budget=policy.support_budget,
            support_scale=policy.support_scale,
            supervising_ministry=policy.supervising_ministry,
            apply_target=policy.apply_target,
            announcement_date=policy.announcement_date,
            biz_process=policy.biz_process,
            application_method=policy.application_method,
            contact_agency=contact_agency,
            contact_number=policy.contact_number,
            required_documents=policy.required_documents,
            collected_date=policy.collected_date,
            created_at=policy.created_at,
            score=score
        )