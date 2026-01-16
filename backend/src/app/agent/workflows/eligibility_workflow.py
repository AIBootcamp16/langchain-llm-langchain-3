"""
Eligibility Workflow
자격 확인 워크플로우 (상태 유지 및 데이터 흐름 강화 버전)
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from ...config.logger import get_logger
from ...observability import trace_workflow, get_feature_tags
from ..state import EligibilityState
from ..nodes.eligibility_nodes import (
    parse_conditions_node,
    check_existing_slots_node,
    generate_checklist_node,
    generate_question_node,
    process_answer_node,
    apply_checklist_node,
    final_decision_node
)

logger = get_logger()

# =========================================================
# 1) 워크플로우 생성 함수
# =========================================================

@trace_workflow(
    name="create_eligibility_start_workflow",
    tags=get_feature_tags("EC"),
    metadata={"workflow_type": "eligibility_start"}
)
def create_eligibility_start_workflow() -> StateGraph:
    """
    자격 확인 시작 워크플로우 (분석 및 체크리스트 생성)
    구조: START → parse_conditions → check_existing_slots → generate_checklist → END
    """
    try:
        # EligibilityState 규격을 사용하여 그래프 생성
        workflow = StateGraph(EligibilityState)

        workflow.add_node("parse_conditions", parse_conditions_node)
        workflow.add_node("check_existing_slots", check_existing_slots_node)
        workflow.add_node("generate_checklist", generate_checklist_node)
        workflow.add_node("generate_question", generate_question_node)

        workflow.set_entry_point("parse_conditions")
        workflow.add_edge("parse_conditions", "check_existing_slots")
        workflow.add_edge("check_existing_slots", "generate_checklist")
        workflow.add_edge("generate_checklist", "generate_question")
        workflow.add_edge("generate_question", END)

        return workflow
    except Exception as e:
        logger.error(f"Error creating eligibility start workflow: {str(e)}", exc_info=True)
        raise

@trace_workflow(
    name="create_eligibility_result_workflow",
    tags=get_feature_tags("EC"),
    metadata={"workflow_type": "eligibility_result"}
)
def create_eligibility_result_workflow() -> StateGraph:
    """
    자격 확인 결과 워크플로우 (사용자 선택 반영 및 최종 판정)
    구조: START → apply_checklist → final_decision → END
    """
    try:
        workflow = StateGraph(EligibilityState)
        
        workflow.add_node("apply_checklist", apply_checklist_node)
        workflow.add_node("final_decision", final_decision_node)
        
        workflow.set_entry_point("apply_checklist")
        workflow.add_edge("apply_checklist", "final_decision")
        workflow.add_edge("final_decision", END)
        
        return workflow
    except Exception as e:
        logger.error(f"Error creating eligibility result workflow: {str(e)}", exc_info=True)
        raise

# =========================================================
# 2) 실행 함수 (API에서 호출)
# =========================================================

def run_eligibility_start(
    session_id: str,
    policy_id: int,
    apply_target: str
) -> Dict[str, Any]:
    """
    자격 확인 프로세스 시작: 정책을 분석하고 UI용 체크리스트를 생성합니다.
    """
    try:
        app = create_eligibility_start_workflow().compile()
        
        # 초기 상태 정의: 모든 필드를 명시적으로 초기화하여 에러 방지
        initial_state: EligibilityState = {
            "session_id": session_id,
            "policy_id": policy_id,
            "apply_target": apply_target,
            "conditions": [], # 여기서 추출된 조건들이 담깁니다.
            "extra_requirements": None,
            "checklist": [], # UI에 뿌려줄 데이터
            "checklist_result": [],
            "user_slots": {},
            "current_question": "",
            "current_condition_index": 0,
            "final_result": "CANNOT_DETERMINE",
            "reason": ""
        }
        
        # 분석 결과(conditions가 채워진 상태)를 반환
        return app.invoke(initial_state)
        
    except Exception as e:
        logger.error(f"Error in run_eligibility_start: {str(e)}", exc_info=True)
        return {"error": str(e), "session_id": session_id}

def run_eligibility_answer(
    session_id: str,
    user_answer: str,
    current_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    사용자 답변을 처리하고 다음 질문을 생성합니다.
    """
    try:
        if not current_state.get("conditions"):
            logger.warning(f"No conditions found in current_state for session: {session_id}")

        # 사용자 답변을 상태에 주입
        current_state["user_answer"] = user_answer

        # 답변 처리 → 질문 생성 워크플로우
        workflow = StateGraph(EligibilityState)
        workflow.add_node("process_answer", process_answer_node)
        workflow.add_node("generate_question", generate_question_node)
        workflow.set_entry_point("process_answer")
        workflow.add_edge("process_answer", "generate_question")
        workflow.add_edge("generate_question", END)

        app = workflow.compile()
        result = app.invoke(current_state)

        # 모든 조건이 확인되었는지 체크
        conditions = result.get("conditions", [])
        unknown_count = sum(1 for c in conditions if c.get("status") == "UNKNOWN")
        result["completed"] = unknown_count == 0

        return result

    except Exception as e:
        logger.error(f"Error in run_eligibility_answer: {str(e)}", exc_info=True)
        return {"error": str(e), "session_id": session_id}


def run_eligibility_result(
    session_id: str,
    current_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    최종 자격 판정을 수행합니다.
    """
    try:
        if not current_state.get("conditions"):
            logger.warning(f"No conditions found in current_state for session: {session_id}")

        app = create_eligibility_result_workflow().compile()
        return app.invoke(current_state)

    except Exception as e:
        logger.error(f"Error in run_eligibility_result: {str(e)}", exc_info=True)
        return {"error": str(e), "session_id": session_id}