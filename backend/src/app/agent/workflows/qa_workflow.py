"""
Q&A Workflow
LangGraph 기반 정책 Q&A 워크플로우 (개선된 버전)
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...config.logger import get_logger
from ...observability import trace_workflow, get_feature_tags
from ..state import QAState
from ..nodes import (
    classify_query_type_node,
    load_cached_docs_node,
    check_sufficiency_node,
    web_search_node,
    generate_answer_with_docs_node,
    generate_answer_web_only_node,
    generate_answer_hybrid_node
)

logger = get_logger()


def route_by_query_type(state: Dict[str, Any]) -> Literal["web_search_for_link", "load_cached_docs"]:
    """
    질문 유형에 따라 다음 노드 결정
    
    WEB_ONLY: 링크/홈페이지 요청 → 웹 검색만 수행
    POLICY_QA: 정책 내용 질문 → 캐시된 문서 조회
    
    Args:
        state: 현재 상태
    
    Returns:
        str: 다음 노드 이름
    """
    query_type = state.get("query_type", "POLICY_QA")
    
    if query_type == "WEB_ONLY":
        logger.info("Routing to web_search_for_link (WEB_ONLY)")
        return "web_search_for_link"
    else:
        logger.info("Routing to load_cached_docs (POLICY_QA)")
        return "load_cached_docs"


def route_by_sufficiency(state: Dict[str, Any]) -> Literal["web_search_supplement", "generate_answer_with_docs"]:
    """
    문서 충분성에 따라 다음 노드 결정
    
    sufficient: 문서만으로 답변 생성
    insufficient: 웹 검색 보완 후 하이브리드 답변 생성
    
    Args:
        state: 현재 상태
    
    Returns:
        str: 다음 노드 이름
    """
    need_web_search = state.get("need_web_search", False)
    
    if need_web_search:
        logger.info("Routing to web_search_supplement (insufficient docs)")
        return "web_search_supplement"
    else:
        logger.info("Routing to generate_answer_with_docs (sufficient docs)")
        return "generate_answer_with_docs"


@trace_workflow(
    name="create_qa_workflow",
    tags=get_feature_tags("QA"),
    metadata={"workflow_type": "qa", "version": "v2_cache"}
)
def create_qa_workflow() -> StateGraph:
    """
    Q&A 워크플로우 생성 (개선된 버전)
    
    워크플로우 구조:
    
    [공고 선택 시 - API 레벨]
    POST /chat/init-policy → 정책 문서 전체 캐시에 저장 (1회)
    
    [사용자 질문마다]
    START → classify_query_type
               ↓
        [WEB_ONLY] ──────────────→ web_search_for_link → generate_answer_web_only → END
               ↓
        [POLICY_QA]
               ↓
        load_cached_docs (캐시에서 문서 조회, Qdrant 검색 없음!)
               ↓
        check_sufficiency
               ↓
        [sufficient] → generate_answer_with_docs → END
               ↓
        [insufficient] → web_search_supplement → generate_answer_hybrid → END
    
    Returns:
        StateGraph: 컴파일된 워크플로우
    """
    try:
        # Create StateGraph
        workflow = StateGraph(QAState)
        
        # Add nodes
        workflow.add_node("classify_query_type", classify_query_type_node)
        workflow.add_node("load_cached_docs", load_cached_docs_node)
        workflow.add_node("check_sufficiency", check_sufficiency_node)
        workflow.add_node("web_search_for_link", web_search_node)  # WEB_ONLY용
        workflow.add_node("web_search_supplement", web_search_node)  # POLICY_QA 보완용
        workflow.add_node("generate_answer_with_docs", generate_answer_with_docs_node)
        workflow.add_node("generate_answer_web_only", generate_answer_web_only_node)
        workflow.add_node("generate_answer_hybrid", generate_answer_hybrid_node)
        
        # Set entry point
        workflow.set_entry_point("classify_query_type")
        
        # Conditional routing by query type
        workflow.add_conditional_edges(
            "classify_query_type",
            route_by_query_type,
            {
                "web_search_for_link": "web_search_for_link",
                "load_cached_docs": "load_cached_docs"
            }
        )
        
        # WEB_ONLY path
        workflow.add_edge("web_search_for_link", "generate_answer_web_only")
        workflow.add_edge("generate_answer_web_only", END)
        
        # POLICY_QA path
        workflow.add_edge("load_cached_docs", "check_sufficiency")
        
        # Conditional routing by sufficiency
        workflow.add_conditional_edges(
            "check_sufficiency",
            route_by_sufficiency,
            {
                "web_search_supplement": "web_search_supplement",
                "generate_answer_with_docs": "generate_answer_with_docs"
            }
        )
        
        # Sufficient path
        workflow.add_edge("generate_answer_with_docs", END)
        
        # Insufficient path (with web supplement)
        workflow.add_edge("web_search_supplement", "generate_answer_hybrid")
        workflow.add_edge("generate_answer_hybrid", END)
        
        logger.info("Q&A workflow created successfully (v2 with cache)")
        
        return workflow
        
    except Exception as e:
        logger.error(
            "Error creating Q&A workflow",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


@trace_workflow(
    name="run_qa_workflow",
    tags=get_feature_tags("QA"),
    metadata={"action": "invoke", "version": "v2_cache"}
)
def run_qa_workflow(
    session_id: str,
    policy_id: int,
    user_query: str,
    messages: list[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Q&A 워크플로우 실행 (개선된 버전)
    
    Args:
        session_id: 세션 ID
        policy_id: 정책 ID
        user_query: 사용자 질문
        messages: 대화 이력 (캐시에서 가져온 것)
    
    Returns:
        Dict: 워크플로우 실행 결과 (answer, evidence 포함)
    """
    try:
        # Create workflow
        workflow = create_qa_workflow()
        
        # Compile with memory
        memory = MemorySaver()
        app = workflow.compile(checkpointer=memory)
        
        # Initial state
        initial_state: QAState = {
            "session_id": session_id,
            "policy_id": policy_id,
            "messages": messages or [],
            "current_query": user_query,
            "query_type": "POLICY_QA",  # classify_query_type_node에서 결정
            "policy_info": {},  # load_cached_docs_node에서 설정
            "retrieved_docs": [],
            "web_sources": [],
            "answer": "",
            "need_web_search": False,
            "evidence": [],
            "error": None
        }
        
        # Run workflow
        config = {"configurable": {"thread_id": session_id}}
        result = app.invoke(initial_state, config=config)
        
        logger.info(
            "Q&A workflow completed",
            extra={
                "session_id": session_id,
                "policy_id": policy_id,
                "query_type": result.get("query_type"),
                "has_answer": bool(result.get("answer"))
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Error running Q&A workflow",
            extra={
                "session_id": session_id,
                "policy_id": policy_id,
                "error": str(e)
            },
            exc_info=True
        )
        return {
            "session_id": session_id,
            "policy_id": policy_id,
            "answer": f"죄송합니다. 워크플로우 실행 중 오류가 발생했습니다: {str(e)}",
            "evidence": [],
            "error": str(e)
        }
