"""
Eligibility Workflow
자격 확인 워크플로우
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from ...config.logger import get_logger
from ...observability import trace_workflow, get_feature_tags
from ..state import EligibilityState
from ..nodes.eligibility_nodes import (
    parse_conditions_node,
    check_existing_slots_node,
    generate_question_node,
    process_answer_node,
    final_decision_node
)

logger = get_logger()

def should_continue(state: Dict[str, Any]) -> Literal["generate_question", "final_decision"]:
    """
    질문 계속 여부 결정
    
    Args:
        state: 현재 상태
    
    Returns:
        str: 다음 노드 이름
    """
    conditions = state.get("conditions", [])
    current_index = state.get("current_condition_index", 0)
    
    # Check if there are more UNKNOWN conditions
    has_more_unknown = any(
        c["status"] == "UNKNOWN" 
        for c in conditions[current_index:]
    )
    
    if has_more_unknown:
        logger.info("More questions needed, routing to generate_question")
        return "generate_question"
    else:
        logger.info("All conditions checked, routing to final_decision")
        return "final_decision"


@trace_workflow(
    name="create_eligibility_start_workflow",
    tags=get_feature_tags("EC"),
    metadata={"workflow_type": "eligibility_start"}
)
def create_eligibility_start_workflow() -> StateGraph:
    """
    자격 확인 시작 워크플로우 생성
    
    워크플로우 구조:
    START → parse_conditions → check_existing_slots → generate_question → END
    
    Returns:
        StateGraph: 컴파일된 워크플로우
    """
    try:
        # Create StateGraph
        workflow = StateGraph(EligibilityState)
        
        # Add nodes
        workflow.add_node("parse_conditions", parse_conditions_node)
        workflow.add_node("check_existing_slots", check_existing_slots_node)
        workflow.add_node("generate_question", generate_question_node)
        
        # Set entry point
        workflow.set_entry_point("parse_conditions")
        
        # Add edges
        workflow.add_edge("parse_conditions", "check_existing_slots")
        workflow.add_edge("check_existing_slots", "generate_question")
        workflow.add_edge("generate_question", END)
        
        logger.info("Eligibility start workflow created successfully")
        
        return workflow
        
    except Exception as e:
        logger.error(
            "Error creating eligibility start workflow",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


@trace_workflow(
    name="create_eligibility_answer_workflow",
    tags=get_feature_tags("EC"),
    metadata={"workflow_type": "eligibility_answer"}
)
def create_eligibility_answer_workflow() -> StateGraph:
    """
    자격 확인 답변 처리 워크플로우 생성
    
    워크플로우 구조:
    START → process_answer → [condition] → generate_question | final_decision → END
    
    Returns:
        StateGraph: 컴파일된 워크플로우
    """
    try:
        # Create StateGraph
        workflow = StateGraph(EligibilityState)
        
        # Add nodes
        workflow.add_node("process_answer", process_answer_node)
        workflow.add_node("generate_question", generate_question_node)
        workflow.add_node("final_decision", final_decision_node)
        
        # Set entry point
        workflow.set_entry_point("process_answer")
        
        # process_answer → check if more questions needed
        workflow.add_conditional_edges(
            "process_answer",
            should_continue,
            {
                "generate_question": "generate_question",
                "final_decision": "final_decision"
            }
        )
        
        # Edges to END
        workflow.add_edge("generate_question", END)
        workflow.add_edge("final_decision", END)
        
        logger.info("Eligibility answer workflow created successfully")
        
        return workflow
        
    except Exception as e:
        logger.error(
            "Error creating eligibility answer workflow",
            extra={"error": str(e)},
            exc_info=True
        )
        raise


@trace_workflow(
    name="run_eligibility_start",
    tags=get_feature_tags("EC"),
    metadata={"action": "start"}
)
def run_eligibility_start(
    session_id: str,
    policy_id: int,
    apply_target: str
) -> Dict[str, Any]:
    """
    자격 확인 시작
    
    Args:
        session_id: 세션 ID
        policy_id: 정책 ID
        apply_target: 신청 대상 텍스트
    
    Returns:
        Dict: 첫 번째 질문 포함
    """
    try:
        # Create start workflow
        workflow = create_eligibility_start_workflow()
        
        # Compile (no memory needed for start)
        app = workflow.compile()
        
        # Initial state
        initial_state: EligibilityState = {
            "session_id": session_id,
            "policy_id": policy_id,
            "apply_target": apply_target,
            "conditions": [],
            "user_slots": {},
            "current_question": "",
            "current_condition_index": 0,
            "final_result": "ELIGIBLE",
            "reason": ""
        }
        
        # Run workflow to generate first question
        result = app.invoke(initial_state)
        
        logger.info(
            "Eligibility start completed",
            extra={
                "session_id": session_id,
                "policy_id": policy_id,
                "conditions_count": len(result.get("conditions", []))
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(
            "Error running eligibility start",
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
            "current_question": "죄송합니다. 자격 확인 시작 중 오류가 발생했습니다.",
            "conditions": [],
            "error": str(e)
        }


@trace_workflow(
    name="run_eligibility_answer",
    tags=get_feature_tags("EC"),
    metadata={"action": "answer"}
)
def run_eligibility_answer(
    session_id: str,
    user_answer: str,
    current_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    자격 확인 답변 처리
    
    Args:
        session_id: 세션 ID
        user_answer: 사용자 답변
        current_state: 현재 상태
    
    Returns:
        Dict: 다음 질문 또는 최종 결과
    """
    try:
        # Add user answer to state
        current_state["user_answer"] = user_answer
        
        # Process answer
        state_after_process = process_answer_node(current_state)
        
        # Check if more questions needed
        conditions = state_after_process.get("conditions", [])
        current_index = state_after_process.get("current_condition_index", 0)
        
        has_more_unknown = any(
            c["status"] == "UNKNOWN" 
            for c in conditions[current_index:]
        )
        
        if has_more_unknown:
            # Generate next question
            state_with_question = generate_question_node(state_after_process)
            
            logger.info(
                "Next question generated",
                extra={
                    "session_id": session_id,
                    "condition_index": state_with_question.get("current_condition_index")
                }
            )
            
            return {
                **state_with_question,
                "completed": False
            }
        else:
            # Final decision
            final_state = final_decision_node(state_after_process)
            
            logger.info(
                "Eligibility check completed",
                extra={
                    "session_id": session_id,
                    "result": final_state.get("final_result")
                }
            )
            
            return {
                **final_state,
                "completed": True
            }
        
    except Exception as e:
        logger.error(
            "Error running eligibility answer",
            extra={
                "session_id": session_id,
                "error": str(e)
            },
            exc_info=True
        )
        return {
            "session_id": session_id,
            "current_question": "죄송합니다. 답변 처리 중 오류가 발생했습니다.",
            "completed": False,
            "error": str(e)
        }