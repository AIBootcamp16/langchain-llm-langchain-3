"""
Q&A Workflow
LangGraph 기반 정책 Q&A 워크플로우
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...config.logger import get_logger
from ...observability import trace_workflow, get_feature_tags
from ..state import QAState
from ..nodes import (
    classify_query_node,
    retrieve_from_db_node,
    check_sufficiency_node,
    web_search_node,
    generate_answer_node
)

logger = get_logger()


def should_web_search(state: Dict[str, Any]) -> Literal["web_search", "generate_answer"]:
    """
    웹 검색 필요 여부에 따라 다음 노드 결정
    
    Args:
        state: 현재 상태
    
    Returns:
        str: 다음 노드 이름
    """
    need_web_search = state.get("need_web_search", False)
    
    if need_web_search:
        logger.info("Routing to web_search node")
        return "web_search"
    else:
        logger.info("Routing directly to generate_answer node")
        return "generate_answer"


@trace_workflow(
    name="create_qa_workflow",
    tags=get_feature_tags("QA"),
    metadata={"workflow_type": "qa"}
)
def create_qa_workflow() -> StateGraph:
    """
    Q&A 워크플로우 생성
    
    워크플로우 구조:
    START → classify_query → retrieve_from_db → check_sufficiency
                                                      ↓
                                web_search ← [insufficient] | [sufficient] → generate_answer → END
                                      ↓
                                 generate_answer → END
    
    Returns:
        StateGraph: 컴파일된 워크플로우
    """
    try:
        # Create StateGraph
        workflow = StateGraph(QAState)
        
        # Add nodes
        workflow.add_node("classify_query", classify_query_node)
        workflow.add_node("retrieve_from_db", retrieve_from_db_node)
        workflow.add_node("check_sufficiency", check_sufficiency_node)
        workflow.add_node("web_search", web_search_node)
        workflow.add_node("generate_answer", generate_answer_node)
        
        # Set entry point
        workflow.set_entry_point("classify_query")
        
        # Add edges
        workflow.add_edge("classify_query", "retrieve_from_db")
        workflow.add_edge("retrieve_from_db", "check_sufficiency")
        
        # Conditional edge: check_sufficiency → web_search or generate_answer
        workflow.add_conditional_edges(
            "check_sufficiency",
            should_web_search,
            {
                "web_search": "web_search",
                "generate_answer": "generate_answer"
            }
        )
        
        # web_search → generate_answer
        workflow.add_edge("web_search", "generate_answer")
        
        # generate_answer → END
        workflow.add_edge("generate_answer", END)
        
        logger.info("Q&A workflow created successfully")
        
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
    metadata={"action": "invoke"}
)
def run_qa_workflow(
    session_id: str,
    policy_id: int,
    user_query: str,
    messages: list[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Q&A 워크플로우 실행
    
    Args:
        session_id: 세션 ID
        policy_id: 정책 ID
        user_query: 사용자 질문
        messages: 대화 이력 (선택)
    
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

