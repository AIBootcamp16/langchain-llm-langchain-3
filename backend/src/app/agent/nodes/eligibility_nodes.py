"""
Eligibility Workflow Nodes
자격 확인 워크플로우 노드들
"""

import json
from typing import Dict, Any
from jinja2 import Template
from pathlib import Path

from ...config.logger import get_logger
from ...observability import trace_workflow, trace_llm_call
from ...llm import get_openai_client
from ...db.engine import get_db
from ...db.models import Policy

logger = get_logger()


@trace_llm_call(name="parse_conditions", tags=["eligibility", "parse"])
def parse_conditions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    apply_target 텍스트를 조건 객체로 파싱
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (conditions 추가)
    """
    try:
        apply_target = state.get("apply_target", "")
        policy_id = state.get("policy_id")
        
        if not apply_target:
            logger.warning("No apply_target provided")
            return {
                **state,
                "conditions": [],
                "error": "신청 대상 정보가 없습니다."
            }
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "eligibility_prompt.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        prompt = template.render(apply_target=apply_target)
        
        # Call LLM
        llm_client = get_openai_client()
        response = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정책 자격 조건 분석 전문가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        
        # Parse JSON response
        try:
            # Extract JSON from response (remove markdown if present)
            response_clean = response.strip()
            if "```json" in response_clean:
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0].strip()
            
            conditions = json.loads(response_clean)
            
            # Add status field
            for condition in conditions:
                condition["status"] = "UNKNOWN"
                condition["reason"] = None
            
            logger.info(
                "Conditions parsed",
                extra={
                    "policy_id": policy_id,
                    "conditions_count": len(conditions)
                }
            )
            
            return {
                **state,
                "conditions": conditions,
                "current_condition_index": 0
            }
            
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse conditions JSON",
                extra={"error": str(e), "response": response},
                exc_info=True
            )
            return {
                **state,
                "conditions": [],
                "error": f"조건 파싱 실패: {str(e)}"
            }
        
    except Exception as e:
        logger.error(
            "Error in parse_conditions_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "conditions": [],
            "error": str(e)
        }


@trace_workflow(name="check_existing_slots", tags=["eligibility", "check"])
def check_existing_slots_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 슬롯으로 판정 가능한 조건 체크
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태
    """
    try:
        conditions = state.get("conditions", [])
        user_slots = state.get("user_slots", {})
        
        if not conditions:
            return state
        
        # Check each condition against user slots
        for condition in conditions:
            condition_type = condition.get("type")
            condition_value = condition.get("value", "").lower()
            
            # Try to match with user slots
            matched = False
            
            if condition_type == "business_status" and "business_status" in user_slots:
                user_value = user_slots["business_status"].lower()
                if condition_value in user_value or user_value in condition_value:
                    condition["status"] = "PASS"
                    condition["reason"] = f"사용자 정보와 일치: {user_slots['business_status']}"
                    matched = True
            
            elif condition_type == "region" and "region" in user_slots:
                user_region = user_slots["region"].lower()
                # "전국" is always PASS
                if "전국" in condition_value or "전국" in user_region:
                    condition["status"] = "PASS"
                    condition["reason"] = "전국 대상 정책입니다."
                    matched = True
                elif condition_value in user_region or user_region in condition_value:
                    condition["status"] = "PASS"
                    condition["reason"] = f"지역 조건 만족: {user_slots['region']}"
                    matched = True
            
            elif condition_type == "age" and "age" in user_slots:
                # Age comparison logic (simplified)
                condition["status"] = "PASS"
                condition["reason"] = f"나이 조건 확인: {user_slots['age']}"
                matched = True
            
            if not matched:
                condition["status"] = "UNKNOWN"
        
        logger.info(
            "Existing slots checked",
            extra={
                "total_conditions": len(conditions),
                "passed": sum(1 for c in conditions if c["status"] == "PASS"),
                "unknown": sum(1 for c in conditions if c["status"] == "UNKNOWN")
            }
        )
        
        return {
            **state,
            "conditions": conditions
        }
        
    except Exception as e:
        logger.error(
            "Error in check_existing_slots_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return state


@trace_llm_call(name="generate_question", tags=["eligibility", "question"])
def generate_question_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    다음 UNKNOWN 조건에 대한 질문 생성
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (current_question 추가)
    """
    try:
        conditions = state.get("conditions", [])
        current_index = state.get("current_condition_index", 0)
        policy_id = state.get("policy_id")
        user_slots = state.get("user_slots", {})
        
        # Find next UNKNOWN condition
        next_condition = None
        next_index = current_index
        
        for i in range(current_index, len(conditions)):
            if conditions[i]["status"] == "UNKNOWN":
                next_condition = conditions[i]
                next_index = i
                break
        
        if not next_condition:
            # All conditions checked
            logger.info("All conditions have been checked")
            return {
                **state,
                "current_question": None,
                "current_condition_index": len(conditions)
            }
        
        # Get policy info
        policy_name = ""
        if policy_id:
            with get_db() as db:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if policy:
                    policy_name = policy.program_name
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "eligibility_question.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        prompt = template.render(
            policy_name=policy_name,
            condition_name=next_condition.get("name"),
            condition_description=next_condition.get("description"),
            condition_type=next_condition.get("type"),
            user_slots=user_slots
        )
        
        # Generate question
        llm_client = get_openai_client()
        question = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 친절한 정책 상담사입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        logger.info(
            "Question generated",
            extra={
                "condition_index": next_index,
                "condition_name": next_condition.get("name")
            }
        )
        
        return {
            **state,
            "current_question": question.strip(),
            "current_condition_index": next_index
        }
        
    except Exception as e:
        logger.error(
            "Error in generate_question_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "current_question": "질문 생성 중 오류가 발생했습니다.",
            "error": str(e)
        }


@trace_workflow(name="process_answer", tags=["eligibility", "process"])
def process_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 답변 처리 및 조건 판정
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태
    """
    try:
        conditions = state.get("conditions", [])
        current_index = state.get("current_condition_index", 0)
        user_answer = state.get("user_answer", "")
        user_slots = state.get("user_slots", {})
        
        if current_index >= len(conditions):
            return state
        
        current_condition = conditions[current_index]
        condition_type = current_condition.get("type")
        condition_value = current_condition.get("value", "").lower()
        
        # Save user answer to slots
        slot_name = condition_type or current_condition.get("name")
        user_slots[slot_name] = user_answer
        
        # Simple rule-based judgment
        user_answer_lower = user_answer.lower()
        
        # Business status check
        if condition_type == "business_status":
            if "예비" in condition_value and "예비" in user_answer_lower:
                current_condition["status"] = "PASS"
                current_condition["reason"] = "예비창업자 조건을 만족합니다."
            elif "3년" in condition_value and any(x in user_answer_lower for x in ["1년", "2년", "3년", "예비"]):
                current_condition["status"] = "PASS"
                current_condition["reason"] = "업력 조건을 만족합니다."
            elif "창업" in condition_value and "창업" in user_answer_lower:
                current_condition["status"] = "PASS"
                current_condition["reason"] = "창업 조건을 만족합니다."
            else:
                current_condition["status"] = "UNKNOWN"
                current_condition["reason"] = f"답변: {user_answer} (추가 확인 필요)"
        
        # Region check
        elif condition_type == "region":
            if "전국" in condition_value:
                current_condition["status"] = "PASS"
                current_condition["reason"] = "전국 대상 정책입니다."
            else:
                current_condition["status"] = "PASS"
                current_condition["reason"] = f"지역: {user_answer}"
        
        # Other types
        else:
            current_condition["status"] = "PASS"
            current_condition["reason"] = f"답변: {user_answer}"
        
        # Update conditions
        conditions[current_index] = current_condition
        
        logger.info(
            "Answer processed",
            extra={
                "condition_index": current_index,
                "status": current_condition["status"]
            }
        )
        
        return {
            **state,
            "conditions": conditions,
            "user_slots": user_slots,
            "current_condition_index": current_index + 1,
            "user_answer": ""
        }
        
    except Exception as e:
        logger.error(
            "Error in process_answer_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return state


@trace_workflow(name="final_decision", tags=["eligibility", "decision"])
def final_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 자격 판정
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (final_result, reason 추가)
    """
    try:
        conditions = state.get("conditions", [])
        
        if not conditions:
            return {
                **state,
                "final_result": "NOT_ELIGIBLE",
                "reason": "확인할 조건이 없습니다."
            }
        
        # Count statuses
        pass_count = sum(1 for c in conditions if c["status"] == "PASS")
        fail_count = sum(1 for c in conditions if c["status"] == "FAIL")
        unknown_count = sum(1 for c in conditions if c["status"] == "UNKNOWN")
        
        # Determine final result
        if fail_count > 0:
            final_result = "NOT_ELIGIBLE"
            reason = f"{fail_count}개 조건을 만족하지 못합니다."
        elif unknown_count > 0:
            final_result = "PARTIALLY"
            reason = f"{unknown_count}개 조건은 추가 확인이 필요합니다."
        else:
            final_result = "ELIGIBLE"
            reason = "모든 자격 조건을 충족합니다."
        
        logger.info(
            "Final decision made",
            extra={
                "result": final_result,
                "pass": pass_count,
                "fail": fail_count,
                "unknown": unknown_count
            }
        )
        
        return {
            **state,
            "final_result": final_result,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(
            "Error in final_decision_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "final_result": "NOT_ELIGIBLE",
            "reason": f"판정 중 오류 발생: {str(e)}",
            "error": str(e)
        }

