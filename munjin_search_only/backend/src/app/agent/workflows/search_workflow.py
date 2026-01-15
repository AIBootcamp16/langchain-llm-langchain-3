"""
Search Workflow
LangGraph 기반 정책 검색 워크플로우 (성능 최적화 버전)

워크플로우 구조 (간소화):
START → query_understanding → retrieve → check_sufficiency
                                                ↓
              finalize ← [충분] | [부족] → web_search → finalize → END

성능 최적화:
- summarize 노드 제거 (LLM 호출 감소)
- finalize 노드로 결과 병합만 수행
- 3단계 충분성 검증 (Top-K → Cosine → LLM Grader)
"""

import time
from typing import Dict, Any, Literal, List
import uuid
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...config.logger import get_logger
from ...observability import trace_workflow, get_feature_tags
from ..state import SearchState
from ..nodes.search import (
    query_understanding_node,
    search_retrieve_node,
    search_check_sufficiency_node,
    search_web_search_node,
)

logger = get_logger()


def should_web_search(state: Dict[str, Any]) -> Literal["web_search", "finalize"]:
    """
    충분성 검사 결과에 따라 다음 노드 결정

    Args:
        state: 현재 상태

    Returns:
        str: 다음 노드 이름 ("web_search" 또는 "finalize")
    """
    is_sufficient = state.get("is_sufficient", False)

    if is_sufficient:
        logger.info(
            "Search results sufficient, routing to finalize",
            extra={"reason": state.get("sufficiency_reason", "")[:100]}
        )
        return "finalize"
    else:
        logger.info(
            "Search results insufficient, routing to web_search",
            extra={"reason": state.get("sufficiency_reason", "")[:100]}
        )
        return "web_search"


@trace_workflow(
    name="finalize_results",
    tags=["node", "search", "finalize"]
)
def finalize_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색 결과를 최종 정리 (LLM 호출 없이 빠르게 처리)

    - retrieved_docs → policies 변환
    - web_sources → policies에 추가 (웹 결과)
    - 간단한 summary 생성 (LLM 없이)

    Args:
        state: 현재 상태

    Returns:
        Dict: 업데이트된 상태 (summary, policies, total_count)
    """
    try:
        original_query = state.get("original_query", "")
        retrieved_docs = state.get("retrieved_docs", [])
        web_sources = state.get("web_sources", [])
        top_score = state.get("top_score", 0.0)

        # Build final policies list from retrieved_docs
        policies: List[Dict[str, Any]] = []
        for doc in retrieved_docs:
            policy = {
                "id": doc.get("policy_id"),
                "program_id": doc.get("policy_id"),
                "program_name": doc.get("program_name"),
                "program_overview": doc.get("program_overview"),
                "region": doc.get("region"),
                "category": doc.get("category"),
                "support_description": doc.get("support_description"),
                "support_budget": doc.get("support_budget"),
                "apply_target": doc.get("apply_target"),
                "announcement_date": doc.get("announcement_date"),
                "application_method": doc.get("application_method"),
                "score": doc.get("score"),
                "source_type": "internal"
            }
            policies.append(policy)

        # Add web sources as supplementary results (웹 결과가 있는 경우)
        for idx, source in enumerate(web_sources):
            web_policy = {
                "id": -1000 - idx,  # Negative ID for web results
                "program_id": -1,
                "program_name": source.get("title", "웹 검색 결과"),
                "program_overview": source.get("snippet", ""),
                "region": "웹 검색",
                "category": "웹 검색 결과",
                "support_description": f"출처: {source.get('url', '')}",
                "support_budget": None,
                "apply_target": "웹 검색 결과 - 자세한 내용은 출처 링크를 확인하세요",
                "announcement_date": source.get("fetched_date"),
                "application_method": source.get("url"),
                "score": source.get("score", 0.5),
                "source_type": "web",
                "url": source.get("url")
            }
            policies.append(web_policy)

        total_count = len(policies)
        internal_count = len(retrieved_docs)
        web_count = len(web_sources)

        # Generate simple summary (LLM 없이)
        if internal_count > 0:
            top_policy = retrieved_docs[0].get("program_name", "정책")
            if top_score >= 0.7:
                summary = f"'{original_query}' 검색 결과 {total_count}건을 찾았습니다. '{top_policy}'이(가) 가장 관련도가 높습니다(유사도: {top_score:.0%})."
            else:
                summary = f"'{original_query}' 검색 결과 {total_count}건을 찾았습니다."

            if web_count > 0:
                summary += f" 웹 검색으로 {web_count}건의 추가 정보를 확인했습니다."
        elif web_count > 0:
            summary = f"'{original_query}'에 대한 내부 정책을 찾지 못해 웹 검색 결과 {web_count}건을 제공합니다."
        else:
            summary = f"'{original_query}'에 대한 검색 결과가 없습니다."

        logger.info(
            "Finalize results completed",
            extra={
                "total_policies": total_count,
                "internal_count": internal_count,
                "web_count": web_count
            }
        )

        return {
            **state,
            "summary": summary,
            "policies": policies,
            "total_count": total_count
        }

    except Exception as e:
        logger.error(
            "Error in finalize_results_node",
            extra={"error": str(e)},
            exc_info=True
        )
        # 에러 시에도 기본 결과 반환
        retrieved_docs = state.get("retrieved_docs", [])
        policies = [
            {
                "id": doc.get("policy_id"),
                "program_id": doc.get("policy_id"),
                "program_name": doc.get("program_name"),
                "region": doc.get("region"),
                "category": doc.get("category"),
                "score": doc.get("score"),
                "source_type": "internal"
            }
            for doc in retrieved_docs
        ]

        return {
            **state,
            "summary": f"검색 결과 {len(policies)}건을 찾았습니다.",
            "policies": policies,
            "total_count": len(policies),
            "error": str(e)
        }


@trace_workflow(
    name="create_search_workflow",
    tags=get_feature_tags("SEARCH"),
    metadata={"workflow_type": "search", "version": "2.0-optimized"}
)
def create_search_workflow() -> StateGraph:
    """
    Search 워크플로우 생성 (성능 최적화 버전)

    워크플로우 구조:
    1. query_understanding: LLM으로 쿼리 분석 (의도, 키워드, 필터 추출)
    2. retrieve: Qdrant + MySQL 하이브리드 검색
    3. check_sufficiency: 3단계 충분성 검사 (Top-K → Cosine → LLM Grader)
    4. [조건부] web_search: 불충분 시 웹 검색
    5. finalize: 결과 병합 및 간단한 요약 (LLM 없이)

    Returns:
        StateGraph: 컴파일된 워크플로우
    """
    try:
        # Create StateGraph with SearchState
        workflow = StateGraph(SearchState)

        # Add nodes (summarize 제거, finalize 추가)
        workflow.add_node("query_understanding", query_understanding_node)
        workflow.add_node("retrieve", search_retrieve_node)
        workflow.add_node("check_sufficiency", search_check_sufficiency_node)
        workflow.add_node("web_search", search_web_search_node)
        workflow.add_node("finalize", finalize_results_node)

        # Set entry point
        workflow.set_entry_point("query_understanding")

        # Add edges
        workflow.add_edge("query_understanding", "retrieve")
        workflow.add_edge("retrieve", "check_sufficiency")

        # Conditional edge: check_sufficiency → web_search or finalize
        workflow.add_conditional_edges(
            "check_sufficiency",
            should_web_search,
            {
                "web_search": "web_search",
                "finalize": "finalize"
            }
        )

        # web_search → finalize
        workflow.add_edge("web_search", "finalize")

        # finalize → END
        workflow.add_edge("finalize", END)

        logger.info("Search workflow created successfully (v2.0 optimized)")

        return workflow

    except Exception as e:
        logger.error(
            "Error creating search workflow",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


@trace_workflow(
    name="run_search_workflow",
    tags=get_feature_tags("SEARCH"),
    metadata={"action": "invoke", "version": "2.0-optimized"}
)
def run_search_workflow(
    query: str,
    session_id: str = None
) -> Dict[str, Any]:
    """
    Search 워크플로우 실행 (성능 최적화 버전)

    Args:
        query: 검색 쿼리
        session_id: 세션 ID (선택, 없으면 자동 생성)

    Returns:
        Dict: 워크플로우 실행 결과
            - session_id: 세션 ID
            - summary: 검색 결과 요약
            - policies: 정책 리스트
            - total_count: 전체 결과 수
            - parsed_query: 분석된 쿼리 정보
            - top_score: 최고 유사도 점수
            - is_sufficient: 충분성 여부
            - sufficiency_reason: 충분성 판단 사유
            - web_sources: 웹 검색 결과 (불충분 시)
            - grader_result: LLM Grader 결과 (있는 경우)
            - error: 에러 메시지 (선택)
    """
    start_time = time.time()

    try:
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Create workflow
        workflow = create_search_workflow()

        # Compile with memory checkpointer
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)

        # Initial state
        initial_state: SearchState = {
            "session_id": session_id,
            "original_query": query,
            "parsed_query": {},
            "retrieved_docs": [],
            "is_sufficient": False,
            "sufficiency_reason": "",
            "top_score": 0.0,
            "web_sources": [],
            "summary": "",
            "policies": [],
            "total_count": 0,
            "error": None
        }

        # Run workflow
        config = {"configurable": {"thread_id": session_id}}
        result = app.invoke(initial_state, config=config)

        elapsed_time = time.time() - start_time

        logger.info(
            "Search workflow completed",
            extra={
                "session_id": session_id,
                "query": query,
                "total_count": result.get("total_count", 0),
                "is_sufficient": result.get("is_sufficient", False),
                "has_web_sources": len(result.get("web_sources", [])) > 0,
                "elapsed_time_ms": int(elapsed_time * 1000)
            }
        )

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            "Error running search workflow",
            extra={
                "session_id": session_id,
                "query": query,
                "error": str(e),
                "elapsed_time_ms": int(elapsed_time * 1000)
            },
            exc_info=True
        )
        return {
            "session_id": session_id or str(uuid.uuid4()),
            "original_query": query,
            "parsed_query": {},
            "retrieved_docs": [],
            "is_sufficient": False,
            "sufficiency_reason": f"워크플로우 실행 중 오류: {str(e)}",
            "top_score": 0.0,
            "web_sources": [],
            "summary": f"검색 중 오류가 발생했습니다: {str(e)}",
            "policies": [],
            "total_count": 0,
            "error": str(e)
        }
