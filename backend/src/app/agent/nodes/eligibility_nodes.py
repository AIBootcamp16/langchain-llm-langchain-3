import json
import re
from typing import Dict, Any, Optional, Tuple, List
from jinja2 import Template
from pathlib import Path

from ...config.logger import get_logger
from ...observability import trace_workflow, trace_llm_call
from ...llm import get_openai_client
from ...db.engine import get_db
from ...db.models import Policy

logger = get_logger()

# =========================================================
# 0) 헬퍼 함수 및 상수
# =========================================================

# 14대 타입 -> user_slots 키 매핑
TYPE_TO_SLOT_KEY = {
    "Age": "age",
    "Business Age": "business_age",
    "Location": "location",
    "Business Type": "business_type",
    "Experience": "experience",
    "Financial Status": "financial_status",
    "Tech & Innovation": "tech_innovation",
    "Application Type": "application_type",
    "Individual Traits": "individual_traits",
    "Business Objective": "business_objective",
    "Collaboration": "collaboration",
    "Legal & Social": "legal_social",
    "Employment Status": "employment_status",
    "Compliance & Tax": "compliance_tax",
    "business_status": "business_status",
}

def _extract_json_from_llm_response(text: str) -> str:
    """
    LLM 응답에서 ```json ...``` 또는 ``` ...``` 블록이 있으면 그 안만 추출.
    없으면 전체를 JSON으로 가정.
    """
    if not text:
        return ""

    s = text.strip()

    # ```json 블록 처리
    if "```json" in s:
        s = s.split("```json", 1)[1]
        s = s.split("```", 1)[0].strip()
        return s

    # 일반 코드 블록 처리
    if "```" in s:
        parts = s.split("```", 2)
        if len(parts) >= 2:
            s = parts[1].strip()
            # 언어 태그가 첫 줄에 섞여 있을 경우 제거 (예: ```python)
            s_lines = s.splitlines()
            if s_lines and re.match(r"^[a-zA-Z]+$", s_lines[0].strip()):
                s = "\n".join(s_lines[1:]).strip()
            return s
    
    # 텍스트 내에서 가장 바깥쪽의 { } 또는 [ ] 블록을 찾음 (Fallback)
    match = re.search(r'(\{.*\}|\[.*\])', s, re.DOTALL)
    if match:
        return match.group(0).strip()

    return s

def _safe_json_loads(s: str) -> Any:
    """
    JSON 파싱. 실패 시 예외를 그대로 올림.
    """
    return json.loads(s)

def _normalize_text(x: str) -> str:
    return re.sub(r"\s+", " ", (x or "").strip()).lower()

def _judge_with_llm(condition: Dict[str, Any], user_answer: str) -> Tuple[str, str]:
    """
    LLM을 사용하여 사용자 답변이 조건을 충족하는지 판정
    """
    try:
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "eligibility_judge.jinja2"
        if not prompt_path.exists():
            logger.warning("eligibility_judge.jinja2 not found, falling back to UNKNOWN")
            return "UNKNOWN", "판정 프롬프트를 찾을 수 없습니다."

        with open(prompt_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        template = Template(template_str)
        prompt = template.render(
            condition_name=condition.get("name", ""),
            condition_description=condition.get("description", ""),
            condition_type=condition.get("type", ""),
            condition_value=condition.get("value", ""),
            user_answer=user_answer
        )

        # Call LLM
        llm_client = get_openai_client()
        response = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정책 자격 조건 판정 전문가입니다. JSON 형식으로만 응답하세요."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        # Parse response
        response_clean = _extract_json_from_llm_response(response if isinstance(response, str) else response.content)
        result = _safe_json_loads(response_clean)

        status = result.get("status", "UNKNOWN")
        reason = result.get("reason", "")

        # Validate status
        if status not in ("PASS", "FAIL", "UNKNOWN"):
            status = "UNKNOWN"

        return status, reason

    except Exception as e:
        logger.error(f"LLM judgment failed: {e}", exc_info=True)
        return "UNKNOWN", f"LLM 판정 중 오류 발생: {str(e)}"

def _judge_with_slot(condition: Dict[str, Any], user_slots: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    condition + user_slots -> PASS/UNKNOWN/FAIL 판정 (LLM 기반)
    """
    ctype = condition.get("type")
    
    # slot_key 찾기
    slot_key = TYPE_TO_SLOT_KEY.get(ctype)
    if not slot_key:
        slot_key = ctype or condition.get("name") or "unknown"

    # 사용자 답변이 없으면 UNKNOWN
    if slot_key not in user_slots or user_slots.get(slot_key) in (None, ""):
        return "UNKNOWN", None

    user_answer = str(user_slots.get(slot_key))

    # LLM으로 판정
    status, reason = _judge_with_llm(condition, user_answer)
    return status, reason

# =========================================================
# 1) Node: parse_conditions_node (LLM 호출 + 파싱)
# =========================================================
@trace_llm_call(name="parse_conditions", tags=["eligibility", "parse"])
def parse_conditions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    apply_target 텍스트를 14대 표준 스키마 조건 객체로 파싱
    """
    try:
        apply_target = state.get("apply_target", "")
        policy_id = state.get("policy_id")

        if not apply_target:
            logger.warning("No apply_target provided")
            return {
                **state,
                "conditions": [],
                "extra_requirements": None,
                "error": "신청 대상 정보가 없습니다.",
            }

        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "eligibility_prompt.jinja2"
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                template_str = f.read()
            template = Template(template_str)
            prompt = template.render(apply_target=apply_target)
        else:
            prompt = f"다음 텍스트에서 지원 자격 조건을 JSON으로 추출하시오: {apply_target}"

        # Call LLM
        llm_client = get_openai_client()
        response = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정책 자격 조건 분석 전문가입니다. 오직 JSON만 응답합니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        content = response if isinstance(response, str) else response.content

        # Parse JSON response
        try:
            response_clean = _extract_json_from_llm_response(content)
            parsed = _safe_json_loads(response_clean)

            conditions = []
            extra_requirements = None

            # 리스트나 딕셔너리 모두 처리
            if isinstance(parsed, list):
                conditions = parsed
            elif isinstance(parsed, dict):
                conditions = parsed.get("conditions", [])
                extra_requirements = parsed.get("extra_requirements", None)
            else:
                logger.warning("Parsed JSON is neither list nor dict")

            if not isinstance(conditions, list):
                conditions = []

            # status/reason 표준 필드 부여
            valid_conditions = []
            for c in conditions:
                if isinstance(c, dict):
                    c["status"] = c.get("status", "UNKNOWN") or "UNKNOWN"
                    c["reason"] = c.get("reason", None)
                    valid_conditions.append(c)
            
            conditions = valid_conditions

            logger.info(f"Conditions parsed: {len(conditions)} items", extra={"policy_id": policy_id})

            return {
                **state,
                "conditions": conditions,
                "extra_requirements": extra_requirements,
                "current_condition_index": 0,
                "error": None,
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse conditions JSON: {e}", exc_info=True)
            return {
                **state,
                "conditions": [],
                "extra_requirements": "형식 오류로 수동 확인이 필요합니다.",
                "error": f"조건 파싱 실패: {str(e)}",
            }

    except Exception as e:
        logger.error(f"Error in parse_conditions_node: {e}", exc_info=True)
        return {
            **state,
            "conditions": [],
            "error": str(e),
        }

# =========================================================
# 2) Node: check_existing_slots_node (기존 슬롯 기반 자동 판정)
# =========================================================
@trace_workflow(name="check_existing_slots", tags=["eligibility", "check"])
def check_existing_slots_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 user_slots로 판정 가능한 조건들을 PASS/FAIL로 미리 채움
    """
    try:
        conditions = state.get("conditions", []) or []
        user_slots = state.get("user_slots", {}) or {}

        if not conditions:
            return {"current_condition_index": 0}

        for condition in conditions:
            # 이미 판정된 것은 스킵
            if condition.get("status") in ("PASS", "FAIL"):
                continue

            status, reason = _judge_with_slot(condition, user_slots)

            condition["status"] = status
            condition["reason"] = reason

        return {**state, "conditions": conditions, "current_condition_index": 0}

    except Exception as e:
        logger.error(f"Error in check_existing_slots_node: {e}", exc_info=True)
        return state

# =========================================================
# 3) Node: generate_checklist_node (UI용 체크리스트 데이터 생성)
# =========================================================
@trace_workflow(name="generate_checklist", tags=["eligibility", "checklist"])
def generate_checklist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    UI에서 사용할 체크리스트 형태의 데이터를 생성합니다.
    """
    conditions = state.get("conditions", []) or []
    checklist = []
    
    for idx, cond in enumerate(conditions):
        name = (cond.get("name") or "").strip()
        value = (cond.get("value") or "").strip()
        label = f"{name}: {value}" if value and value not in name else name
        
        checklist.append({
            "condition_index": idx,
            "label": label,
            "description": cond.get("description", ""),
            "status": cond.get("status", "UNKNOWN"),
            "selection": None
        })
        
    return {"checklist": checklist}

# =========================================================
# 4) Node: apply_checklist_node (UI 체크리스트 선택 반영)
# =========================================================
@trace_workflow(name="apply_checklist", tags=["eligibility", "apply"])
def apply_checklist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자가 UI에서 선택한 값을 기존 조건 리스트에 맵핑합니다.
    """
    conditions = state.get("conditions") or []
    checklist_result = state.get("checklist_result") or []
    
    # 얕은 복사가 아닌 데이터 갱신을 위해 새 리스트 생성
    updated_conditions = [dict(c) for c in conditions]
    
    for item in checklist_result:
        idx = item.get("condition_index")
        selection = item.get("selection")
        
        if idx is not None and 0 <= idx < len(updated_conditions):
            # 사용자가 선택한 PASS/FAIL/UNKNOWN을 실제 조건 상태에 반영
            if selection in ("PASS", "FAIL", "UNKNOWN"):
                updated_conditions[idx]["status"] = selection
                updated_conditions[idx]["reason"] = "사용자 체크리스트 답변 반영"
                
    return {"conditions": updated_conditions}

# =========================================================
# 5) Node: generate_question_node (대화형 질문 생성)
# =========================================================
@trace_llm_call(name="generate_question", tags=["eligibility", "question"])
def generate_question_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    다음 UNKNOWN 조건에 대한 질문 생성
    """
    try:
        conditions = state.get("conditions", []) or []
        current_index = state.get("current_condition_index", 0)
        policy_id = state.get("policy_id")
        user_slots = state.get("user_slots", {}) or {}

        # Find next UNKNOWN condition
        next_condition = None
        next_index = current_index

        for i in range(current_index, len(conditions)):
            if (conditions[i].get("status") or "UNKNOWN") == "UNKNOWN":
                next_condition = conditions[i]
                next_index = i
                break

        if not next_condition:
            logger.info("All conditions have been checked")
            return {
                **state,
                "current_question": "", 
                "current_condition_index": len(conditions),
            }

        # Get policy info for context
        policy_name = ""
        if policy_id:
            with get_db() as db:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if policy:
                    policy_name = policy.program_name

        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "eligibility_question.jinja2"
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                template_str = f.read()
            template = Template(template_str)
            prompt = template.render(
                policy_name=policy_name,
                condition_name=next_condition.get("name"),
                condition_description=next_condition.get("description"),
                condition_type=next_condition.get("type"),
                user_slots=user_slots,
            )
        else:
            prompt = f"다음 조건에 대해 사용자에게 물어볼 친절한 질문을 작성해줘. 조건: {next_condition.get('description')}"

        # Generate question
        llm_client = get_openai_client()
        question = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 친절한 정책 상담사입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = question if isinstance(question, str) else question.content

        return {
            **state,
            "current_question": content.strip(),
            "current_condition_index": next_index,
        }

    except Exception as e:
        logger.error(f"Error in generate_question_node: {e}", exc_info=True)
        return {
            **state,
            "current_question": "질문 생성 중 오류가 발생했습니다.",
            "error": str(e),
        }

# =========================================================
# 6) Node: process_answer_node (답변 처리 및 판정)
# =========================================================
@trace_workflow(name="process_answer", tags=["eligibility", "process"])
def process_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 답변 처리 및 조건 판정
    """
    try:
        conditions = state.get("conditions", []) or []
        current_index = state.get("current_condition_index", 0)
        user_answer = state.get("user_answer", "") or ""
        user_slots = state.get("user_slots", {}) or {}

        if current_index >= len(conditions):
            return state

        current_condition = conditions[current_index]
        ctype = current_condition.get("type")
        slot_key = TYPE_TO_SLOT_KEY.get(ctype) or (ctype or current_condition.get("name") or "unknown_slot")

        # Save user answer to slots
        user_slots[slot_key] = user_answer

        # Re-judge with updated slot
        status, reason = _judge_with_slot(current_condition, user_slots)

        if status == "UNKNOWN":
            current_condition["status"] = "UNKNOWN"
            current_condition["reason"] = f"{reason or '추가 확인 필요'} | 사용자 답변: {user_answer}"
        else:
            current_condition["status"] = status
            current_condition["reason"] = reason or f"사용자 답변 반영: {user_answer}"

        conditions[current_index] = current_condition

        return {
            **state,
            "conditions": conditions,
            "user_slots": user_slots,
            "current_condition_index": current_index + 1,
            "user_answer": "",
        }

    except Exception as e:
        logger.error(f"Error in process_answer_node: {e}", exc_info=True)
        return state

# =========================================================
# 7) Node: final_decision_node (최종 자격 판정)
# =========================================================
@trace_workflow(name="final_decision", tags=["eligibility", "decision"])
def final_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 자격 판정
    - OR 조건: 하나라도 PASS면 전체 OR 그룹 PASS
    - AND 조건: 모두 PASS여야 전체 PASS
    """
    try:
        conditions = state.get("conditions", []) or []
        extra_requirements = state.get("extra_requirements", None)
        policy_id = state.get("policy_id")

        final_result_mapped = "FAIL"  # Default
        reason = ""

        if not conditions:
            return {
                **state,
                "final_result": "FAIL",
                "reason": "확인할 조건이 없습니다.",
            }

        # OR 조건과 AND 조건 분리
        or_conditions = [c for c in conditions if c.get("logic") == "OR"]
        and_conditions = [c for c in conditions if c.get("logic") != "OR"]

        # OR 조건 평가: 하나라도 PASS면 OR 그룹 전체 PASS
        or_group_pass = False
        or_group_has_unknown = False
        if or_conditions:
            or_pass_count = sum(1 for c in or_conditions if c.get("status") == "PASS")
            or_unknown_count = sum(1 for c in or_conditions if c.get("status") == "UNKNOWN")
            or_group_pass = or_pass_count > 0
            or_group_has_unknown = or_unknown_count > 0 and not or_group_pass
        else:
            or_group_pass = True  # OR 조건 없으면 통과로 간주

        # AND 조건 평가: 모두 PASS여야 함
        and_fail_count = sum(1 for c in and_conditions if c.get("status") == "FAIL")
        and_unknown_count = sum(1 for c in and_conditions if c.get("status") == "UNKNOWN")
        
        # 최종 판정 로직
        if not or_group_pass:
            final_result_mapped = "FAIL"
            reason = "선택 조건(OR) 중 충족하는 항목이 없습니다."
        elif and_fail_count > 0:
            final_result_mapped = "FAIL"
            reason = f"{and_fail_count}개의 필수 요건을 만족하지 못합니다."
        elif or_group_has_unknown or and_unknown_count > 0:
            final_result_mapped = "UNKNOWN"
            reason = "일부 조건은 추가 확인이 필요합니다."
        elif extra_requirements and extra_requirements not in ("null", "None"):
            # 조건은 다 통과했으나, 텍스트로 된 추가 요구사항이 남아있는 경우
            final_result_mapped = "UNKNOWN"
            reason = f"정량 조건은 충족하나, 다음 사항 확인이 필요합니다: {extra_requirements}"
        else:
            final_result_mapped = "ELIGIBLE" # or PASS
            reason = "모든 자격 조건을 충족합니다."

        # DB에서 문의처 정보 가져오기 (UNKNOWN일 때 유용)
        if final_result_mapped == "UNKNOWN" and policy_id:
             with get_db() as db:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if policy:
                    agency = policy.contact_agency or ""
                    number = policy.contact_number or ""
                    if agency or number:
                        reason += f" (문의: {agency} {number})"

        return {
            **state,
            "final_result": final_result_mapped,
            "reason": reason,
        }

    except Exception as e:
        logger.error(f"Error in final_decision_node: {e}", exc_info=True)
        return {
            **state,
            "final_result": "FAIL",
            "reason": f"판정 중 시스템 오류 발생: {str(e)}",
            "error": str(e),
        }