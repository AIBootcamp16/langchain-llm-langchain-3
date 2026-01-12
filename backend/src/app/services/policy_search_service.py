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
        score_threshold: float = 0.7,
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
            policy_responses = []
            total = 0
            
            if query:
                # Vector search with Qdrant
                logger.info(
                    "Performing hybrid search",
                    extra={
                        "query": query,
                        "region": region,
                        "category": category,
                        "limit": limit
                    }
                )
                
                policies = self._vector_search(
                    query=query,
                    region=region,
                    category=category,
                    limit=limit,
                    offset=offset,
                    score_threshold=score_threshold
                )
                
                # Convert to response models
                policy_responses = [
                    self._to_response(policy, score=getattr(policy, 'score', None))
                    for policy in policies
                ]
                total = len(policy_responses)
                
                # DB 검색 결과가 적으면 웹 검색 추가
                if total < min_results_for_web_search:
                    logger.info(
                        "DB results insufficient, performing web search",
                        extra={
                            "db_results": total,
                            "min_required": min_results_for_web_search
                        }
                    )
                    
                    web_results = self._web_search(
                        query=query,
                        max_results=limit - total if total > 0 else limit
                    )
                    
                    if web_results:
                        policy_responses.extend(web_results)
                        total = len(policy_responses)
                        
                        logger.info(
                            "Web search results added",
                            extra={"web_results": len(web_results)}
                        )
                
            else:
                # Direct MySQL search
                logger.info(
                    "Performing direct search",
                    extra={
                        "region": region,
                        "category": category,
                        "limit": limit
                    }
                )
                
                policies = self.policy_repo.search(
                    region=region,
                    category=category,
                    limit=limit,
                    offset=offset
                )
                total = self.policy_repo.count(region=region, category=category)
                
                # Convert to response models
                policy_responses = [
                    self._to_response(policy, score=getattr(policy, 'score', None))
                    for policy in policies
                ]
            
            logger.info(
                "Search completed",
                extra={
                    "results_count": len(policy_responses),
                    "total": total
                }
            )
            
            return policy_responses, total
            
        except Exception as e:
            logger.error(
                "Error in hybrid search",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def _vector_search(
        self,
        query: str,
        region: Optional[str],
        category: Optional[str],
        limit: int,
        offset: int,
        score_threshold: float
    ) -> List[Policy]:
        """
        벡터 검색 수행
        
        Args:
            query: 검색 쿼리
            region: 지역 필터
            category: 카테고리 필터
            limit: 반환 개수
            offset: 오프셋
            score_threshold: 최소 스코어
        
        Returns:
            List[Policy]: 정책 리스트 (score 속성 추가)
        """
        # Generate query embedding
        query_vector = self.embedder.embed_text(query)
        
        # Build filter
        filter_dict = {}
        if region:
            filter_dict["region"] = region
        if category:
            filter_dict["category"] = category
        
        # Search in Qdrant
        results = self.qdrant_manager.search(
            query_vector=query_vector,
            limit=limit * 2,  # Get more results for deduplication
            score_threshold=score_threshold,
            filter_dict=filter_dict if filter_dict else None
        )
        
        # Extract policy IDs and scores
        policy_scores = {}
        for result in results:
            policy_id = result["payload"].get("policy_id")
            score = result["score"]
            
            if policy_id:
                # Keep highest score for each policy
                if policy_id not in policy_scores or score > policy_scores[policy_id]:
                    policy_scores[policy_id] = score
        
        # Get policies from MySQL
        unique_policy_ids = list(policy_scores.keys())
        
        if not unique_policy_ids:
            logger.warning("No policies found in vector search")
            return []
        
        # Fetch policies
        policies = self.db.query(Policy).filter(
            Policy.id.in_(unique_policy_ids)
        ).all()
        
        # Add scores and sort
        for policy in policies:
            policy.score = policy_scores.get(policy.id, 0.0)
        
        policies.sort(key=lambda p: p.score, reverse=True)
        
        # Apply offset and limit
        return policies[offset:offset + limit]
    
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

