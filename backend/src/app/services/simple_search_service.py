"""
Simple Search Service
간소화된 정책 검색 서비스 (LLM 호출 없이 빠른 검색)

기존 Search Agent 워크플로우를 대체하는 단순하고 빠른 검색 서비스
- Dense 벡터 검색 (Qdrant)
- Sparse 키워드 검색 (BM25)
- 하이브리드 검색 (Dense + Sparse)
- 동적 유사도 조정
- 웹 검색 폴백 (Tavily)
- 검색 품질 평가 지표
"""

import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from ..db.models import Policy
from ..db.engine import get_db
from ..vector_store import get_qdrant_manager, get_embedder, get_hybrid_searcher, HybridSearcher
from ..config.logger import get_logger
from ..config import get_settings
from ..observability import trace_workflow, get_feature_tags
from ..web_search.clients.tavily_client import get_tavily_client
from .search_config import get_search_config, SearchConfig, SearchMode

logger = get_logger()
settings = get_settings()


@dataclass
class SearchMetrics:
    """검색 품질 평가 지표"""
    total_candidates: int = 0           # 초기 후보 수
    filtered_count: int = 0             # 필터링 후 결과 수
    final_count: int = 0                # 최종 결과 수
    top_score: float = 0.0              # 최고 유사도
    avg_score: float = 0.0              # 평균 유사도
    min_score: float = 0.0              # 최소 유사도
    score_threshold_used: float = 0.0   # 사용된 유사도 임계값
    web_search_triggered: bool = False  # 웹 검색 수행 여부
    web_search_count: int = 0           # 웹 검색 결과 수
    search_time_ms: int = 0             # 검색 소요 시간 (ms)
    sufficiency_reason: str = ""        # 충분성 판단 사유
    search_mode: str = "hybrid"         # 검색 모드 (dense, sparse, hybrid)
    dense_count: int = 0                # Dense 검색 결과 수
    sparse_count: int = 0               # Sparse 검색 결과 수
    hybrid_count: int = 0               # 둘 다 매칭된 수

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "total_candidates": self.total_candidates,
            "filtered_count": self.filtered_count,
            "final_count": self.final_count,
            "top_score": round(self.top_score, 4),
            "avg_score": round(self.avg_score, 4),
            "min_score": round(self.min_score, 4),
            "score_threshold_used": round(self.score_threshold_used, 4),
            "web_search_triggered": self.web_search_triggered,
            "web_search_count": self.web_search_count,
            "search_time_ms": self.search_time_ms,
            "sufficiency_reason": self.sufficiency_reason,
            "search_mode": self.search_mode,
            "dense_count": self.dense_count,
            "sparse_count": self.sparse_count,
            "hybrid_count": self.hybrid_count
        }


@dataclass
class SearchEvidence:
    """검색 근거 정보"""
    policy_id: int
    matched_content: str                # 매칭된 텍스트 일부
    score: float                        # 유사도 점수
    match_type: str = "vector"          # 매칭 타입 (vector, keyword, hybrid)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "policy_id": self.policy_id,
            "matched_content": self.matched_content[:200] + "..." if len(self.matched_content) > 200 else self.matched_content,
            "score": round(self.score, 4),
            "match_type": self.match_type
        }


class SimpleSearchService:
    """
    간소화된 검색 서비스

    LLM 호출 없이 빠른 벡터 검색 수행
    """

    def __init__(self, config: SearchConfig = None):
        """
        초기화

        Args:
            config: 검색 설정 (None이면 기본 설정 사용)
        """
        self.config = config or get_search_config()
        self.qdrant_manager = get_qdrant_manager()
        self.embedder = get_embedder()
        self.hybrid_searcher = get_hybrid_searcher(
            dense_weight=self.config.dense_weight,
            sparse_weight=self.config.sparse_weight,
            use_rrf=self.config.use_rrf
        )
        self._bm25_index_built = False

    @trace_workflow(
        name="simple_search",
        tags=get_feature_tags("SEARCH"),
        run_type="chain"
    )
    def search(
        self,
        query: str,
        region: Optional[str] = None,
        category: Optional[str] = None,
        target_group: Optional[str] = None,
        session_id: Optional[str] = None,
        include_web_search: bool = True
    ) -> Dict[str, Any]:
        """
        정책 검색 수행

        Args:
            query: 검색 쿼리
            region: 지역 필터
            category: 카테고리 필터
            target_group: 대상 그룹 필터
            session_id: 세션 ID (없으면 자동 생성)
            include_web_search: 웹 검색 포함 여부

        Returns:
            Dict: 검색 결과
                - session_id: 세션 ID
                - summary: 검색 요약
                - policies: 정책 리스트
                - total_count: 전체 결과 수
                - top_score: 최고 유사도
                - web_sources: 웹 검색 결과
                - metrics: 검색 품질 지표
                - evidence: 검색 근거 리스트
        """
        start_time = time.time()
        session_id = session_id or str(uuid.uuid4())

        logger.info(
            "Starting simple search",
            extra={
                "session_id": session_id,
                "query": query,
                "region": region,
                "category": category
            }
        )

        metrics = SearchMetrics()
        evidence_list: List[SearchEvidence] = []
        policies: List[Dict[str, Any]] = []
        web_sources: List[Dict[str, Any]] = []

        try:
            # 1. 키워드 추출 (간단한 규칙 기반)
            keywords = self._extract_keywords(query)

            # 2. 동적 유사도 임계값 계산
            initial_threshold = self.config.calculate_threshold(
                keywords=keywords,
                region=region,
                category=category
            )
            metrics.score_threshold_used = initial_threshold
            metrics.search_mode = self.config.search_mode.value

            # 3. 검색 수행 (모드에 따라 다른 검색 전략)
            if self.config.search_mode == SearchMode.HYBRID:
                # 하이브리드 검색 (Dense + Sparse)
                retrieved_docs, evidence_list = self._hybrid_search(
                    query=query,
                    region=region,
                    category=category,
                    target_group=target_group,
                    score_threshold=initial_threshold,
                    metrics=metrics
                )
            else:
                # Dense 검색만 (기존 방식)
                retrieved_docs, evidence_list = self._vector_search(
                    query=query,
                    region=region,
                    category=category,
                    target_group=target_group,
                    score_threshold=initial_threshold
                )

            metrics.total_candidates = len(retrieved_docs)

            # 4. 결과가 부족하면 임계값 낮춰서 재검색
            if len(retrieved_docs) < self.config.target_min_results:
                lower_threshold = self.config.calculate_threshold(
                    keywords=keywords,
                    region=region,
                    category=category,
                    current_result_count=len(retrieved_docs)
                )

                if lower_threshold < initial_threshold:
                    logger.info(
                        "Lowering threshold for more results",
                        extra={
                            "initial": initial_threshold,
                            "new": lower_threshold,
                            "current_count": len(retrieved_docs)
                        }
                    )
                    metrics.score_threshold_used = lower_threshold

                    if self.config.search_mode == SearchMode.HYBRID:
                        retrieved_docs, evidence_list = self._hybrid_search(
                            query=query,
                            region=region,
                            category=category,
                            target_group=target_group,
                            score_threshold=lower_threshold,
                            metrics=metrics
                        )
                    else:
                        retrieved_docs, evidence_list = self._vector_search(
                            query=query,
                            region=region,
                            category=category,
                            target_group=target_group,
                            score_threshold=lower_threshold
                        )
                    metrics.total_candidates = len(retrieved_docs)

            # 5. 결과 정렬 및 제한
            retrieved_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
            retrieved_docs = retrieved_docs[:self.config.result_limit]
            metrics.filtered_count = len(retrieved_docs)

            # 6. 점수 통계 계산
            if retrieved_docs:
                scores = [doc.get("score", 0) for doc in retrieved_docs]
                metrics.top_score = max(scores)
                metrics.avg_score = sum(scores) / len(scores)
                metrics.min_score = min(scores)

            # 7. 웹 검색 충분성 검사
            should_web_search = (
                include_web_search and
                self.config.should_trigger_web_search(
                    result_count=len(retrieved_docs),
                    top_score=metrics.top_score
                )
            )

            if should_web_search:
                metrics.web_search_triggered = True
                metrics.sufficiency_reason = (
                    f"내부 검색 결과 부족 (결과: {len(retrieved_docs)}건, "
                    f"최고 점수: {metrics.top_score:.2f}). 웹 검색으로 보충합니다."
                )
                web_sources = self._web_search(query, keywords, region, target_group)
                metrics.web_search_count = len(web_sources)
            else:
                metrics.sufficiency_reason = (
                    f"내부 검색 결과 충분 (결과: {len(retrieved_docs)}건, "
                    f"최고 점수: {metrics.top_score:.2f})."
                )

            # 8. 최종 정책 리스트 구성
            for doc in retrieved_docs:
                metadata = doc.get("metadata", {})
                
                # contact_agency가 리스트인 경우 문자열로 변환 (이미 변환되었을 수도 있음)
                contact_agency = metadata.get("contact_agency")
                if isinstance(contact_agency, list):
                    contact_agency = ", ".join(str(item) for item in contact_agency) if contact_agency else None
                
                # application_method가 리스트인 경우 문자열로 변환 (이미 변환되었을 수도 있음)
                application_method = doc.get("application_method")
                if isinstance(application_method, list):
                    application_method = ", ".join(str(item) for item in application_method) if application_method else None
                
                policy = {
                    "id": doc.get("policy_id"),
                    "program_id": doc.get("policy_id"),
                    "program_name": doc.get("program_name") or "",
                    "program_overview": doc.get("program_overview"),
                    "region": doc.get("region"),
                    "category": doc.get("category"),
                    "support_description": doc.get("support_description") or "",
                    "support_budget": doc.get("support_budget"),
                    "support_scale": metadata.get("support_scale"),
                    "supervising_ministry": metadata.get("supervising_ministry"),
                    "apply_target": doc.get("apply_target") or "",
                    "announcement_date": doc.get("announcement_date"),
                    "application_method": application_method,
                    "contact_agency": contact_agency,
                    "created_at": doc.get("created_at"),
                    "score": doc.get("score"),
                    "source_type": "internal"
                }
                policies.append(policy)

            # 웹 검색 결과 추가 (region/category 필터가 적용되지 않은 경우에만)
            # 웹 검색 결과는 필터링할 수 없으므로, 필터가 있으면 제외
            if not region and not category:
                for idx, source in enumerate(web_sources):
                    url = source.get("url", "")
                    
                    # Favicon URL 생성 (Google favicon API 사용)
                    from urllib.parse import urlparse
                    try:
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc
                        favicon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
                    except:
                        favicon_url = ""
                    
                    web_policy = {
                        "id": -1000 - idx,
                        "program_id": -1,
                        "program_name": source.get("title", "웹 검색 결과"),
                        "program_overview": source.get("snippet", ""),
                        "region": "웹 검색",
                        "category": "웹 검색 결과",
                        "support_description": source.get("snippet", ""),
                        "support_budget": None,
                        "support_scale": None,
                        "supervising_ministry": None,
                        "apply_target": "웹 검색 결과 - 자세한 내용은 출처 링크를 확인하세요",
                        "announcement_date": source.get("fetched_date"),
                        "application_method": url,
                        "contact_agency": None,
                        "created_at": source.get("fetched_date"),
                        "score": source.get("score", 0.5),
                        "source_type": "web",
                        "url": url,
                        "favicon_url": favicon_url,
                        "screenshot_url": ""  # 스크린샷은 비활성화 (유료 서비스)
                    }
                    policies.append(web_policy)

            metrics.final_count = len(policies)

            # 9. 검색 요약 생성
            summary = self._generate_summary(
                query=query,
                policies=policies,
                metrics=metrics
            )

            elapsed_time = time.time() - start_time
            metrics.search_time_ms = int(elapsed_time * 1000)

            logger.info(
                "Simple search completed",
                extra={
                    "session_id": session_id,
                    "total_count": metrics.final_count,
                    "search_time_ms": metrics.search_time_ms,
                    "top_score": metrics.top_score,
                    "web_search_triggered": metrics.web_search_triggered
                }
            )

            return {
                "session_id": session_id,
                "original_query": query,
                "summary": summary,
                "policies": policies,
                "total_count": len(policies),
                "top_score": metrics.top_score,
                "is_sufficient": not metrics.web_search_triggered,
                "sufficiency_reason": metrics.sufficiency_reason,
                "web_sources": web_sources,
                "metrics": metrics.to_dict(),
                "evidence": [e.to_dict() for e in evidence_list[:10]],  # 상위 10개만
                "parsed_query": {
                    "intent": "policy_search",
                    "keywords": keywords,
                    "filters": {
                        "region": region,
                        "category": category,
                        "target_group": target_group
                    },
                    "sort_preference": "relevance",
                    "time_context": None
                },
                "error": None
            }

        except Exception as e:
            elapsed_time = time.time() - start_time
            metrics.search_time_ms = int(elapsed_time * 1000)

            logger.error(
                "Error in simple search",
                extra={
                    "session_id": session_id,
                    "query": query,
                    "error": str(e),
                    "search_time_ms": metrics.search_time_ms
                },
                exc_info=True
            )

            return {
                "session_id": session_id,
                "original_query": query,
                "summary": f"검색 중 오류가 발생했습니다: {str(e)}",
                "policies": [],
                "total_count": 0,
                "top_score": 0.0,
                "is_sufficient": False,
                "sufficiency_reason": f"오류: {str(e)}",
                "web_sources": [],
                "metrics": metrics.to_dict(),
                "evidence": [],
                "parsed_query": {
                    "intent": "policy_search",
                    "keywords": [],
                    "filters": {},
                    "sort_preference": "relevance",
                    "time_context": None
                },
                "error": str(e)
            }

    def _extract_keywords(self, query: str) -> List[str]:
        """
        간단한 키워드 추출 (규칙 기반)

        Args:
            query: 검색 쿼리

        Returns:
            List[str]: 키워드 리스트
        """
        # 불용어
        stopwords = {"을", "를", "이", "가", "은", "는", "에", "의", "로", "와", "과", "도", "만", "뿐"}

        # 공백으로 분리 후 필터링
        words = query.split()
        keywords = [w for w in words if w not in stopwords and len(w) > 1]

        return keywords

    def _build_bm25_index_if_needed(self) -> None:
        """
        BM25 인덱스 구축 (필요시)

        처음 하이브리드 검색 호출 시 한 번만 인덱스 구축
        """
        if self._bm25_index_built:
            return

        logger.info("Building BM25 index for hybrid search")

        try:
            # Qdrant에서 모든 문서 조회
            all_docs = self.qdrant_manager.get_all_documents(limit=10000)

            # BM25 인덱스용 문서 준비
            documents = []
            for doc in all_docs:
                payload = doc.get("payload", {})
                policy_id = payload.get("policy_id")
                content = payload.get("content", "")

                if policy_id and content:
                    documents.append({
                        "id": policy_id,
                        "content": content
                    })

            # 중복 제거 (같은 policy_id는 한 번만)
            seen_ids = set()
            unique_docs = []
            for doc in documents:
                if doc["id"] not in seen_ids:
                    unique_docs.append(doc)
                    seen_ids.add(doc["id"])

            # BM25 인덱스 구축
            self.hybrid_searcher.build_sparse_index(unique_docs)
            self._bm25_index_built = True

            logger.info(f"BM25 index built with {len(unique_docs)} documents")

        except Exception as e:
            logger.error(f"Error building BM25 index: {e}", exc_info=True)
            # 인덱스 구축 실패 시 Dense 검색만 사용
            self._bm25_index_built = False

    def _hybrid_search(
        self,
        query: str,
        region: Optional[str],
        category: Optional[str],
        target_group: Optional[str],
        score_threshold: float,
        metrics: SearchMetrics
    ) -> Tuple[List[Dict[str, Any]], List[SearchEvidence]]:
        """
        하이브리드 검색 수행 (Dense + Sparse)

        Args:
            query: 검색 쿼리
            region: 지역 필터
            category: 카테고리 필터
            target_group: 대상 그룹 필터
            score_threshold: 유사도 임계값
            metrics: 검색 지표 (업데이트됨)

        Returns:
            Tuple[List[Dict], List[SearchEvidence]]: (검색 결과, 검색 근거)
        """
        # BM25 인덱스 구축 (처음 한 번만)
        self._build_bm25_index_if_needed()

        # 1. Dense 검색 (벡터)
        query_vector = self.embedder.embed_text(query)

        qdrant_filter = {}
        if region:
            qdrant_filter["region"] = region
        if category:
            qdrant_filter["category"] = category

        dense_results = self.qdrant_manager.search(
            query_vector=query_vector,
            limit=self.config.qdrant_limit,
            score_threshold=score_threshold,
            filter_dict=qdrant_filter if qdrant_filter else None
        )

        # Dense 결과를 (policy_id, score) 형태로 변환
        dense_policy_scores: List[Tuple[int, float]] = []
        policy_contents: Dict[int, str] = {}

        for result in dense_results:
            payload = result.get("payload", {})
            policy_id = payload.get("policy_id")
            score = result.get("score", 0.0)
            content = payload.get("content", "")

            if policy_id:
                # 같은 policy_id가 여러 번 나올 수 있으므로 최고 점수만 유지
                existing = next((i for i, (pid, _) in enumerate(dense_policy_scores) if pid == policy_id), None)
                if existing is not None:
                    if score > dense_policy_scores[existing][1]:
                        dense_policy_scores[existing] = (policy_id, score)
                        policy_contents[policy_id] = content
                else:
                    dense_policy_scores.append((policy_id, score))
                    policy_contents[policy_id] = content

        # 2. Sparse 검색 (BM25)
        sparse_policy_scores: List[Tuple[int, float]] = []

        if self.hybrid_searcher.bm25_index:
            sparse_results = self.hybrid_searcher.bm25_index.search(
                query=query,
                top_k=self.config.qdrant_limit,
                min_score=self.config.sparse_min_score
            )
            sparse_policy_scores = sparse_results

        # 3. 하이브리드 결합
        combined_results = self.hybrid_searcher.combine_results(
            dense_results=dense_policy_scores,
            sparse_results=sparse_policy_scores,
            normalize=True
        )

        # 매칭 타입별 카운트
        for _, _, match_type in combined_results:
            if match_type == "dense":
                metrics.dense_count += 1
            elif match_type == "sparse":
                metrics.sparse_count += 1
            elif match_type == "hybrid":
                metrics.hybrid_count += 1

        logger.info(
            "Hybrid search completed",
            extra={
                "dense_count": len(dense_policy_scores),
                "sparse_count": len(sparse_policy_scores),
                "combined_count": len(combined_results),
                "hybrid_matches": metrics.hybrid_count
            }
        )

        # 4. MySQL에서 정책 상세 정보 조회
        policy_ids = [pid for pid, _, _ in combined_results]
        if not policy_ids:
            return [], []

        # 점수 및 매칭 타입 저장
        policy_scores = {pid: score for pid, score, _ in combined_results}
        policy_match_types = {pid: match_type for pid, _, match_type in combined_results}

        retrieved_docs = []
        evidence_list: List[SearchEvidence] = []

        with get_db() as db:
            policies = db.query(Policy).filter(Policy.id.in_(policy_ids)).all()

            # 필터링 적용
            if region:
                policies = [p for p in policies if p.region == region]
            if category:
                policies = [p for p in policies if p.category == category]
            if target_group:
                policies = [
                    p for p in policies
                    if p.apply_target and target_group in p.apply_target
                ]

            for policy in policies:
                score = policy_scores.get(policy.id, 0.0)
                match_type = policy_match_types.get(policy.id, "hybrid")

                # contact_agency와 application_method가 리스트인 경우 문자열로 변환
                contact_agency = policy.contact_agency
                if isinstance(contact_agency, list):
                    contact_agency = ", ".join(str(item) for item in contact_agency) if contact_agency else None
                
                application_method = policy.application_method
                if isinstance(application_method, list):
                    application_method = ", ".join(str(item) for item in application_method) if application_method else None

                doc = {
                    "policy_id": policy.id,
                    "program_name": policy.program_name,
                    "program_overview": policy.program_overview,
                    "content": policy_contents.get(policy.id, ""),
                    "score": score,
                    "match_type": match_type,
                    "region": policy.region,
                    "category": policy.category,
                    "support_description": policy.support_description,
                    "support_budget": policy.support_budget,
                    "apply_target": policy.apply_target,
                    "announcement_date": policy.announcement_date,
                    "application_method": application_method,
                    "created_at": str(policy.created_at) if policy.created_at else None,
                    "metadata": {
                        "supervising_ministry": policy.supervising_ministry,
                        "support_scale": policy.support_scale,
                        "contact_agency": contact_agency
                    }
                }
                retrieved_docs.append(doc)

                # 검색 근거 추가
                evidence_list.append(SearchEvidence(
                    policy_id=policy.id,
                    matched_content=policy_contents.get(policy.id, policy.program_name or ""),
                    score=score,
                    match_type=match_type
                ))

        # 점수순 정렬
        retrieved_docs.sort(key=lambda x: x.get("score", 0), reverse=True)
        evidence_list.sort(key=lambda x: x.score, reverse=True)

        return retrieved_docs, evidence_list

    def _vector_search(
        self,
        query: str,
        region: Optional[str],
        category: Optional[str],
        target_group: Optional[str],
        score_threshold: float
    ) -> Tuple[List[Dict[str, Any]], List[SearchEvidence]]:
        """
        벡터 검색 수행 (Dense only)

        Args:
            query: 검색 쿼리
            region: 지역 필터
            category: 카테고리 필터
            target_group: 대상 그룹 필터
            score_threshold: 유사도 임계값

        Returns:
            Tuple[List[Dict], List[SearchEvidence]]: (검색 결과, 검색 근거)
        """
        # 쿼리 임베딩 생성
        query_vector = self.embedder.embed_text(query)

        # Qdrant 필터 구성
        qdrant_filter = {}
        if region:
            qdrant_filter["region"] = region
        if category:
            qdrant_filter["category"] = category

        # Qdrant 검색
        results = self.qdrant_manager.search(
            query_vector=query_vector,
            limit=self.config.qdrant_limit,
            score_threshold=score_threshold,
            filter_dict=qdrant_filter if qdrant_filter else None
        )

        # 정책 ID별 최고 점수 및 콘텐츠 추적
        policy_scores: Dict[int, float] = {}
        policy_contents: Dict[int, str] = {}
        evidence_list: List[SearchEvidence] = []

        for result in results:
            payload = result.get("payload", {})
            policy_id = payload.get("policy_id")
            score = result.get("score", 0.0)
            content = payload.get("content", "")

            if policy_id:
                # 최고 점수 유지
                if policy_id not in policy_scores or score > policy_scores[policy_id]:
                    policy_scores[policy_id] = score
                    policy_contents[policy_id] = content

                    # 검색 근거 추가
                    evidence_list.append(SearchEvidence(
                        policy_id=policy_id,
                        matched_content=content,
                        score=score,
                        match_type="vector"
                    ))

        if not policy_scores:
            return [], []

        # MySQL에서 정책 상세 정보 조회
        retrieved_docs = []
        with get_db() as db:
            policy_ids = list(policy_scores.keys())
            policies = db.query(Policy).filter(Policy.id.in_(policy_ids)).all()

            # 필터링 적용
            if region:
                policies = [p for p in policies if p.region == region]
            if category:
                policies = [p for p in policies if p.category == category]
            if target_group:
                policies = [
                    p for p in policies
                    if p.apply_target and target_group in p.apply_target
                ]

            for policy in policies:
                doc = {
                    "policy_id": policy.id,
                    "program_name": policy.program_name,
                    "program_overview": policy.program_overview,
                    "content": policy_contents.get(policy.id, ""),
                    "score": policy_scores.get(policy.id, 0.0),
                    "region": policy.region,
                    "category": policy.category,
                    "support_description": policy.support_description,
                    "support_budget": policy.support_budget,
                    "apply_target": policy.apply_target,
                    "announcement_date": policy.announcement_date,
                    "application_method": policy.application_method,
                    "created_at": str(policy.created_at) if policy.created_at else None,
                    "metadata": {
                        "supervising_ministry": policy.supervising_ministry,
                        "support_scale": policy.support_scale,
                        "contact_agency": policy.contact_agency
                    }
                }
                retrieved_docs.append(doc)

        # 점수순 정렬된 evidence 반환
        evidence_list.sort(key=lambda x: x.score, reverse=True)

        return retrieved_docs, evidence_list

    def _web_search(
        self,
        query: str,
        keywords: List[str],
        region: Optional[str],
        target_group: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        웹 검색 수행 (Tavily)

        Args:
            query: 원본 쿼리
            keywords: 키워드 리스트
            region: 지역
            target_group: 대상 그룹

        Returns:
            List[Dict]: 웹 검색 결과
        """
        if not settings.tavily_api_key:
            logger.warning("Tavily API key not configured, skipping web search")
            return []

        try:
            # 검색 쿼리 구성
            search_parts = []

            if keywords:
                search_parts.extend(keywords[:3])
            else:
                search_parts.append(query)

            if region and region != "전국":
                search_parts.append(region)
            if target_group:
                search_parts.append(target_group)

            search_parts.append("정부 지원 사업")
            search_query = " ".join(search_parts)

            # Tavily 검색
            tavily_client = get_tavily_client()
            results = tavily_client.search(
                query=search_query,
                max_results=self.config.web_search_max_results,
                search_depth="advanced"
            )

            web_sources = []
            for result in results:
                web_sources.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("content", ""),
                    "score": result.get("score", 0.0),
                    "fetched_date": date.today().isoformat(),
                    "source_type": "tavily"
                })

            logger.info(
                "Web search completed",
                extra={
                    "query": search_query,
                    "results_count": len(web_sources)
                }
            )

            return web_sources

        except Exception as e:
            logger.error(
                "Error in web search",
                extra={"error": str(e)},
                exc_info=True
            )
            return []

    def _generate_summary(
        self,
        query: str,
        policies: List[Dict[str, Any]],
        metrics: SearchMetrics
    ) -> str:
        """
        검색 요약 생성 (LLM 없이)

        Args:
            query: 검색 쿼리
            policies: 정책 리스트
            metrics: 검색 지표

        Returns:
            str: 검색 요약
        """
        internal_count = sum(1 for p in policies if p.get("source_type") == "internal")
        web_count = sum(1 for p in policies if p.get("source_type") == "web")
        total = len(policies)

        if total == 0:
            return f"'{query}'에 대한 검색 결과가 없습니다."

        if internal_count > 0:
            top_policy = policies[0].get("program_name", "정책")
            if metrics.top_score >= 0.5:
                summary = (
                    f"'{query}' 검색 결과 {total}건을 찾았습니다. "
                    f"'{top_policy}'이(가) 가장 관련도가 높습니다 (유사도: {metrics.top_score:.0%})."
                )
            else:
                summary = f"'{query}' 검색 결과 {total}건을 찾았습니다."

            if web_count > 0:
                summary += f" 웹 검색으로 {web_count}건의 추가 정보를 확인했습니다."
        else:
            summary = (
                f"'{query}'에 대한 내부 정책을 찾지 못해 "
                f"웹 검색 결과 {web_count}건을 제공합니다."
            )

        return summary


# 싱글톤 인스턴스
_simple_search_service: Optional[SimpleSearchService] = None


def get_simple_search_service() -> SimpleSearchService:
    """
    SimpleSearchService 싱글톤 인스턴스 반환

    Returns:
        SimpleSearchService: 검색 서비스 인스턴스
    """
    global _simple_search_service
    if _simple_search_service is None:
        _simple_search_service = SimpleSearchService()
    return _simple_search_service
