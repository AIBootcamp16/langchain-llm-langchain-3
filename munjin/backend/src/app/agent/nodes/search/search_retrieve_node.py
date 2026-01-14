"""
Search Retrieve Node
Qdrant 벡터 검색 + MySQL 메타데이터 조회

성능 최적화:
- score_threshold 0.45로 낮춰 더 많은 후보 확보
- 캐싱된 embedder/qdrant manager 사용
- 불필요한 필드 조회 최소화
"""

import time
from typing import Dict, Any, List, Optional
from sqlalchemy import desc
from sqlalchemy.orm import load_only

from ....config.logger import get_logger
from ....observability import trace_retrieval, get_feature_tags
from ....vector_store import get_qdrant_manager, get_embedder
from ....db.engine import get_db
from ....db.models import Policy

logger = get_logger()

# 검색 성능 상수
QDRANT_LIMIT = 30           # Qdrant에서 가져올 최대 개수
SCORE_THRESHOLD = 0.45      # 낮은 threshold로 더 많은 후보 확보
RESULT_LIMIT = 10           # 최종 반환 결과 수


@trace_retrieval(
    name="search_retrieve",
    tags=["node", "search", "retrieval", "qdrant", "mysql"]
)
def search_retrieve_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Qdrant 벡터 검색 + MySQL 메타데이터 필터링을 통한 정책 검색

    검색 로직:
    1. parsed_query에서 키워드와 필터 추출
    2. 키워드로 임베딩 생성
    3. Qdrant에서 벡터 유사도 검색
    4. MySQL에서 메타데이터 필터링 (region, category)
    5. sort_preference에 따라 정렬

    Args:
        state: 현재 상태 (parsed_query 필수)

    Returns:
        Dict: 업데이트된 상태 (retrieved_docs 추가)
    """
    try:
        parsed_query = state.get("parsed_query", {})
        original_query = state.get("original_query", "")

        keywords = parsed_query.get("keywords", [])
        filters = parsed_query.get("filters", {})
        sort_preference = parsed_query.get("sort_preference", "relevance")

        # Build search query from keywords
        search_query = " ".join(keywords) if keywords else original_query

        if not search_query:
            logger.warning("No search query available")
            return {
                **state,
                "retrieved_docs": [],
                "top_score": 0.0
            }

        # Generate query embedding
        embedder = get_embedder()
        query_vector = embedder.embed_text(search_query)

        # Build Qdrant filter
        qdrant_filter = {}
        if filters.get("region"):
            qdrant_filter["region"] = filters["region"]
        if filters.get("category"):
            qdrant_filter["category"] = filters["category"]

        # Search in Qdrant (성능 최적화: 캐싱된 manager 사용)
        start_time = time.time()
        qdrant_manager = get_qdrant_manager()
        results = qdrant_manager.search(
            query_vector=query_vector,
            limit=QDRANT_LIMIT,  # 더 많은 후보 확보
            score_threshold=SCORE_THRESHOLD,  # 낮은 threshold로 더 많은 후보 확보
            filter_dict=qdrant_filter if qdrant_filter else None
        )
        qdrant_time = time.time() - start_time
        logger.debug(f"Qdrant search took {qdrant_time:.3f}s, found {len(results)} results")

        # Extract unique policy IDs with their best scores
        policy_scores: Dict[int, float] = {}
        policy_contents: Dict[int, str] = {}

        for result in results:
            payload = result.get("payload", {})
            policy_id = payload.get("policy_id")
            score = result.get("score", 0.0)
            content = payload.get("content", "")

            if policy_id:
                # Keep highest score and corresponding content
                if policy_id not in policy_scores or score > policy_scores[policy_id]:
                    policy_scores[policy_id] = score
                    policy_contents[policy_id] = content

        if not policy_scores:
            logger.info("No results from Qdrant search")
            return {
                **state,
                "retrieved_docs": [],
                "top_score": 0.0
            }

        # Fetch policy details from MySQL
        with get_db() as db:
            policy_ids = list(policy_scores.keys())
            policies = db.query(Policy).filter(Policy.id.in_(policy_ids)).all()

            # Additional filtering by target_group (in apply_target field)
            target_group = filters.get("target_group")
            if target_group:
                policies = [
                    p for p in policies
                    if p.apply_target and target_group in p.apply_target
                ]

            # Build retrieved_docs with full information
            retrieved_docs = []
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

            # Sort by preference
            if sort_preference == "latest":
                # Sort by created_at descending
                retrieved_docs.sort(
                    key=lambda x: x.get("created_at") or "",
                    reverse=True
                )
            elif sort_preference == "budget_desc":
                # Sort by support_budget descending
                retrieved_docs.sort(
                    key=lambda x: x.get("support_budget") or 0,
                    reverse=True
                )
            else:
                # Default: sort by relevance score
                retrieved_docs.sort(
                    key=lambda x: x.get("score", 0.0),
                    reverse=True
                )

            # Limit to top RESULT_LIMIT
            retrieved_docs = retrieved_docs[:RESULT_LIMIT]

            # Calculate top score
            top_score = max((d.get("score", 0.0) for d in retrieved_docs), default=0.0)

        logger.info(
            "Search retrieval completed",
            extra={
                "query": search_query,
                "total_results": len(retrieved_docs),
                "top_score": top_score,
                "sort_preference": sort_preference,
                "filters_applied": bool(qdrant_filter)
            }
        )

        return {
            **state,
            "retrieved_docs": retrieved_docs,
            "top_score": top_score
        }

    except Exception as e:
        logger.error(
            "Error in search_retrieve_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "retrieved_docs": [],
            "top_score": 0.0,
            "error": str(e)
        }
