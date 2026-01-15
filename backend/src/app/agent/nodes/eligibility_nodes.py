import json
import re
from typing import Dict, Any, Optional, List
from jinja2 import Template
from pathlib import Path

from ...config.logger import get_logger
from ...observability import trace_workflow, trace_llm_call
from ...llm import get_openai_client
from ...db.engine import get_db
from ...db.models import Policy

logger = get_logger()

# =========================================================
# 0) 헬퍼 함수 (JSON 추출 및 안전한 파싱)
# =========================================================
def _extract_json_from_llm_response(text: str) -> str:
    if not text: return ""
    
    # 텍스트 내에서 가장 바깥쪽의 { } 블록을 찾습니다.
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        s = match.group(0)
        s = re.sub(r"```json|```", "", s).strip()
        return s
    return text.strip()

def _safe_json_loads(s: str) -> Dict[str, Any]:
    try:
        if not s:
            return {"conditions": [], "extra_requirements": "분석 결과가 비어있습니다."}
        return json.loads(s)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 실패: {str(e)} | 추출된 텍스트: {s[:100]}...")
        return {"conditions": [], "extra_requirements": "형식 오류로 수동 확인이 필요합니다."}

# =========================================================
# 1) Node: parse_conditions_node (LLM 기반 조건 추출)
# =========================================================
@trace_llm_call(name="parse_conditions", tags=["eligibility", "parse"])
def parse_conditions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        apply_target = state.get("apply_target", "")
        if not apply_target:
            return {"conditions": [], "extra_requirements": "신청 대상 정보 없음"}

        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "eligibility_prompt.jinja2"
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = Template(f.read())
        prompt = template.render(apply_target=apply_target)

        llm_client = get_openai_client()
        response = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정책 자격 조건 분석 전문가입니다. 오직 JSON만 응답합니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        content = response if isinstance(response, str) else response.content
        response_clean = _extract_json_from_llm_response(content)
        parsed = _safe_json_loads(response_clean)

        conditions = parsed.get("conditions", [])
        extra_req = parsed.get("extra_requirements", None)

        updated_conditions = []
        for c in conditions:
            if isinstance(c, dict):
                # 기본 상태를 UNKNOWN으로 설정하여 사용자 확인 유도
                c["status"] = c.get("status", "UNKNOWN") or "UNKNOWN"
                c["reason"] = None
                updated_conditions.append(c)

        return {
            "conditions": updated_conditions,
            "extra_requirements": extra_req,
            "current_condition_index": 0
        }
    except Exception as e:
        logger.error(f"Error in parse_conditions_node: {str(e)}", exc_info=True)
        return {"conditions": [], "extra_requirements": f"분석 오류 발생: {str(e)}"}

# =========================================================
# 2) Node: check_existing_slots_node (자동 판정)
# =========================================================
@trace_workflow(name="check_existing_slots", tags=["eligibility", "check"])
def check_existing_slots_node(state: Dict[str, Any]) -> Dict[str, Any]:
    return {"current_condition_index": 0}

# =========================================================
# 3) Node: generate_checklist_node (UI용 데이터 생성)
# =========================================================
@trace_workflow(name="generate_checklist", tags=["eligibility", "checklist"])
def generate_checklist_node(state: Dict[str, Any]) -> Dict[str, Any]:
    conditions = state.get("conditions", []) or []
    checklist = []
    
    for idx, cond in enumerate(conditions):
        name = (cond.get("name") or "").strip()
        value = (cond.get("value") or "").strip()
        label = f"{name}: {value}" if value and value not in name else name
        
        checklist.append({
            "condition_index": idx,
            "label": label,
            "selection": None
        })
        
    return {"checklist": checklist}

# =========================================================
# 4) Node: apply_checklist_node (사용자 선택 반영)
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
# 5) Node: final_decision_node (최종 자격 판정)
# =========================================================
@trace_workflow(name="final_decision", tags=["eligibility", "decision"])
def final_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    모든 조건이 PASS인 경우에만 ELIGIBLE을 반환합니다.
    """
    conditions = state.get("conditions") or []
    extra_req = state.get("extra_requirements", None)
    policy_id = state.get("policy_id")

    # 1. 하나라도 부적격(FAIL)이 있는 경우
    if any(c.get("status") == "FAIL" for c in conditions):
        return {"final_result": "NOT_ELIGIBLE", "reason": "필수 요건 중 부적격 항목이 있습니다."}

    # 2. 모든 조건이 PASS인 경우 (데이터가 존재해야 함)
    if conditions and all(c.get("status") == "PASS" for c in conditions):
        return {"final_result": "ELIGIBLE", "reason": "제시된 모든 자격 조건을 충족합니다."}

    # 3. 그 외 (UNKNOWN이 있거나, 추가 요건이 있거나, 조건 자체가 추출되지 않은 경우)
    contact_info = "공고문 참조"
    if policy_id:
        with get_db() as db:
            policy = db.query(Policy).filter(Policy.id == policy_id).first()
            if policy:
                # DB의 contact_agency 및 contact_number 정보를 취합
                agency = policy.contact_agency if policy.contact_agency else ""
                number = policy.contact_number if policy.contact_number else ""
                if agency or number:
                    contact_info = f"{agency} {number}".strip()

    return {
        "final_result": "CANNOT_DETERMINE", 
        "reason": f"추가 확인이 필요한 요건이 있습니다. 상세 내용은 문의처({contact_info})로 확인 부탁드립니다."
    }