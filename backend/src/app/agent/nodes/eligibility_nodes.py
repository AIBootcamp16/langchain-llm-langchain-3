import json
import re
from typing import Dict, Any, Optional, Tuple
from jinja2 import Template
from pathlib import Path

from ...config.logger import get_logger
from ...observability import trace_workflow, trace_llm_call
from ...llm import get_openai_client
from ...db.engine import get_db
from ...db.models import Policy

logger = get_logger()


# =========================================================
# 0) 헬퍼: LLM JSON 추출/파싱
# =========================================================
def _extract_json_from_llm_response(text: str) -> str:
    """
    LLM 응답에서 ```json ...``` 또는 ``` ...``` 블록이 있으면 그 안만 추출.
    없으면 전체를 JSON으로 가정.
    """
    if not text:
        return ""

    s = text.strip()

    if "```json" in s:
        s = s.split("```json", 1)[1]
        s = s.split("```", 1)[0].strip()
        return s

    if "```" in s:
        # 첫 코드블럭만 추출
        parts = s.split("```", 2)
        if len(parts) >= 2:
            s = parts[1].strip()
            # 언어 태그가 들어있으면 첫 줄 제거
            s_lines = s.splitlines()
            if s_lines and re.match(r"^[a-zA-Z]+$", s_lines[0].strip()):
                s = "\n".join(s_lines[1:]).strip()
            return s

    return s


def _safe_json_loads(s: str) -> Any:
    """
    JSON 파싱. 실패 시 예외를 그대로 올림.
    """
    return json.loads(s)


# =========================================================
# 1) 14대 타입 -> user_slots 키 매핑
# =========================================================
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
}


# =========================================================
# 2) 간단 판정 유틸 (RULE-BASED)
# =========================================================
def _normalize_text(x: str) -> str:
    return re.sub(r"\s+", " ", (x or "").strip()).lower()


def _extract_age_constraint(cond_value: str) -> Tuple[Optional[int], Optional[int]]:
    """
    '만 39세 이하', '39세 이하', '만 19세 이상' 같은 텍스트에서 (min_age, max_age)를 추정.
    - 매우 보수적으로: 명확한 패턴만 처리
    """
    v = _normalize_text(cond_value)

    min_age = None
    max_age = None

    # 예: 만 19세 이상 / 19세 이상
    m = re.search(r"(만\s*)?(\d{1,3})\s*세\s*이상", v)
    if m:
        min_age = int(m.group(2))

    # 예: 만 39세 이하 / 39세 이하 / 39세 미만(=38 이하로 보긴 애매 -> max_age=38은 위험하니 UNKNOWN)
    m = re.search(r"(만\s*)?(\d{1,3})\s*세\s*이하", v)
    if m:
        max_age = int(m.group(2))

    return min_age, max_age


def _parse_year_constraint(cond_value: str) -> Optional[Tuple[Optional[int], Optional[int]]]:
    """
    '3년 이내', '3년 초과 7년 이내' 같은 업력 제약에서 (min_year, max_year) 추정
    - min_year: "초과"가 있으면 하한
    - max_year: "이내"가 있으면 상한
    """
    v = _normalize_text(cond_value)

    # 3년 이내
    m1 = re.search(r"(\d+)\s*년\s*이내", v)
    # 3년 초과 7년 이내
    m2 = re.search(r"(\d+)\s*년\s*초과\s*(\d+)\s*년\s*이내", v)

    if m2:
        min_y = int(m2.group(1))  # "초과"는 엄밀히 +epsilon이지만, 룰베이스에선 숫자만 기록
        max_y = int(m2.group(2))
        return (min_y, max_y)

    if m1:
        return (None, int(m1.group(1)))

    return None


def _judge_with_slot(condition: Dict[str, Any], user_slots: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """
    condition(type/name/value/description) + user_slots로
    PASS/UNKNOWN를 최대한 보수적으로 판정.
    (FAIL은 사용자 답변을 받은 후에만 명확히 내리는 걸 권장하지만,
     여기서는 기존 슬롯 매칭 단계이므로 FAIL은 거의 쓰지 않음)
    """
    ctype = condition.get("type")
    cvalue = condition.get("value") or ""
    cdesc = condition.get("description") or ""

    slot_key = TYPE_TO_SLOT_KEY.get(ctype)
    if not slot_key:
        return "UNKNOWN", None

    if slot_key not in user_slots or user_slots.get(slot_key) in (None, ""):
        return "UNKNOWN", None

    user_val_raw = str(user_slots.get(slot_key))
    user_val = _normalize_text(user_val_raw)

    # Location: "전국"은 항상 PASS
    if ctype == "Location":
        cv = _normalize_text(cvalue or cdesc)
        if "전국" in cv:
            return "PASS", "전국 대상 조건입니다."
        # 사용자가 서울/성북구 등 입력했다면 포함관계로 PASS
        if user_val and (user_val in cv or cv in user_val):
            return "PASS", f"사용자 location({user_val_raw})가 조건과 일치/포함됩니다."
        return "UNKNOWN", f"사용자 location({user_val_raw})와 조건의 일치 여부 추가 확인 필요"

    # Age: 숫자 비교 가능한 경우만 PASS
    if ctype == "Age":
        # user_slots['age']가 숫자(나이)로 들어오는 케이스를 기대
        try:
            user_age = int(re.findall(r"\d+", user_val_raw)[0])
        except Exception:
            return "UNKNOWN", f"사용자 age({user_val_raw})가 숫자로 해석되지 않아 추가 확인 필요"

        min_age, max_age = _extract_age_constraint(cvalue or cdesc)
        if min_age is None and max_age is None:
            return "UNKNOWN", "연령 조건이 명확한 숫자 패턴이 아니라 추가 확인 필요"

        if min_age is not None and user_age < min_age:
            return "FAIL", f"나이 {user_age}세는 최소 {min_age}세 이상 조건을 충족하지 않음"
        if max_age is not None and user_age > max_age:
            return "FAIL", f"나이 {user_age}세는 최대 {max_age}세 이하 조건을 충족하지 않음"

        return "PASS", f"나이 {user_age}세가 연령 조건 범위에 포함"

    # Business Age: 업력 비교 가능한 경우만 PASS/FAIL
    if ctype == "Business Age":
        # user_slots['business_age']가 "2년" 또는 "24개월" 같은 형태일 수 있음 -> 숫자만 우선 추출
        years = None
        if re.search(r"\d+\s*년", user_val):
            years = int(re.findall(r"\d+", user_val)[0])
        elif re.search(r"\d+\s*개월", user_val):
            months = int(re.findall(r"\d+", user_val)[0])
            years = months / 12.0

        yr_rng = _parse_year_constraint(cvalue or cdesc)
        if years is None or yr_rng is None:
            # 텍스트 포함관계라도 있으면 PASS
            cv = _normalize_text(cvalue or cdesc)
            if user_val and (user_val in cv or cv in user_val):
                return "PASS", f"사용자 업력({user_val_raw})이 조건 텍스트와 일치/포함"
            return "UNKNOWN", "업력 숫자 비교가 어려워 추가 확인 필요"

        min_y, max_y = yr_rng
        if min_y is not None and years <= min_y:
            # '초과'이므로 <= 는 FAIL 취급 (보수)
            return "FAIL", f"업력({user_val_raw})은 '{min_y}년 초과' 조건을 충족하지 않을 수 있음"
        if max_y is not None and years > max_y:
            return "FAIL", f"업력({user_val_raw})은 '{max_y}년 이내' 조건을 초과"

        return "PASS", f"업력({user_val_raw})이 조건 범위로 판정됨"

    # 나머지 타입: 포함관계로만 약하게 PASS, 아니면 UNKNOWN
    cv = _normalize_text(cvalue or cdesc)
    if user_val and (user_val in cv or cv in user_val):
        return "PASS", f"사용자 {slot_key}({user_val_raw})가 조건 텍스트와 일치/포함"
    return "UNKNOWN", f"사용자 {slot_key}({user_val_raw})로는 자동 판정 불가(추가 확인 필요)"


# =========================================================
# 3) Node: parse_conditions_node (LLM 호출 + 파싱)
# =========================================================
@trace_llm_call(name="parse_conditions", tags=["eligibility", "parse"])
def parse_conditions_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    apply_target 텍스트를 14대 표준 스키마 조건 객체로 파싱

    기대 출력(JSON):
    {
      "conditions": [
        { "type": "Age", "name": "...", "value": "...", "status": "UNKNOWN" }
      ],
      "extra_requirements": null | "..."
    }
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
        with open(prompt_path, "r", encoding="utf-8") as f:
            template_str = f.read()

        template = Template(template_str)
        prompt = template.render(apply_target=apply_target)

        # Call LLM
        llm_client = get_openai_client()
        response = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정책 자격 조건 분석 전문가입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )

        # Parse JSON response
        try:
            response_clean = _extract_json_from_llm_response(response)
            parsed = _safe_json_loads(response_clean)

            # ---- 새 포맷 검증/정규화 ----
            if not isinstance(parsed, dict):
                raise json.JSONDecodeError("Response JSON is not an object", response_clean, 0)

            conditions = parsed.get("conditions", [])
            extra_requirements = parsed.get("extra_requirements", None)

            if not isinstance(conditions, list):
                conditions = []

            # status/reason 표준 필드 부여
            for c in conditions:
                if isinstance(c, dict):
                    c["status"] = c.get("status", "UNKNOWN") or "UNKNOWN"
                    c["reason"] = c.get("reason", None)
                # dict가 아니면 제거
            conditions = [c for c in conditions if isinstance(c, dict)]

            logger.info(
                "Conditions parsed",
                extra={
                    "policy_id": policy_id,
                    "conditions_count": len(conditions),
                    "has_extra_requirements": bool(extra_requirements),
                },
            )

            return {
                **state,
                "conditions": conditions,
                "extra_requirements": extra_requirements,
                "current_condition_index": 0,
                "error": None,
            }

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse conditions JSON",
                extra={"error": str(e), "response": response},
                exc_info=True,
            )
            return {
                **state,
                "conditions": [],
                "extra_requirements": None,
                "error": f"조건 파싱 실패: {str(e)}",
            }

    except Exception as e:
        logger.error(
            "Error in parse_conditions_node",
            extra={"error": str(e)},
            exc_info=True,
        )
        return {
            **state,
            "conditions": [],
            "extra_requirements": None,
            "error": str(e),
        }


# =========================================================
# 4) Node: check_existing_slots_node (기존 슬롯 기반 자동 판정)
# =========================================================
@trace_workflow(name="check_existing_slots", tags=["eligibility", "check"])
def check_existing_slots_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    기존 user_slots로 판정 가능한 조건들을 PASS/FAIL로 미리 채움
    - 보수적으로: 명확하지 않으면 UNKNOWN 유지
    """
    try:
        conditions = state.get("conditions", []) or []
        user_slots = state.get("user_slots", {}) or {}

        if not conditions:
            return state

        for condition in conditions:
            # 이미 판정된 것은 스킵
            if condition.get("status") in ("PASS", "FAIL"):
                continue

            status, reason = _judge_with_slot(condition, user_slots)

            # 기존 단계에서는 FAIL은 다소 공격적일 수 있으나,
            # Age/Business Age처럼 숫자 비교가 명확하면 FAIL을 허용
            condition["status"] = status
            condition["reason"] = reason

        logger.info(
            "Existing slots checked",
            extra={
                "total_conditions": len(conditions),
                "passed": sum(1 for c in conditions if c.get("status") == "PASS"),
                "failed": sum(1 for c in conditions if c.get("status") == "FAIL"),
                "unknown": sum(1 for c in conditions if c.get("status") == "UNKNOWN"),
            },
        )

        return {**state, "conditions": conditions}

    except Exception as e:
        logger.error(
            "Error in check_existing_slots_node",
            extra={"error": str(e)},
            exc_info=True,
        )
        return state


# =========================================================
# 5) Node: generate_question_node (다음 UNKNOWN 조건 질문 생성)
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
                "current_question": None,
                "current_condition_index": len(conditions),
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

        # Generate question
        llm_client = get_openai_client()
        question = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 친절한 정책 상담사입니다."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        logger.info(
            "Question generated",
            extra={
                "condition_index": next_index,
                "condition_name": next_condition.get("name"),
                "condition_type": next_condition.get("type"),
            },
        )

        return {
            **state,
            "current_question": question.strip(),
            "current_condition_index": next_index,
        }

    except Exception as e:
        logger.error(
            "Error in generate_question_node",
            extra={"error": str(e)},
            exc_info=True,
        )
        return {
            **state,
            "current_question": "질문 생성 중 오류가 발생했습니다.",
            "error": str(e),
        }


# =========================================================
# 6) Node: process_answer_node (사용자 답변 저장 + 조건 판정)
# =========================================================
@trace_workflow(name="process_answer", tags=["eligibility", "process"])
def process_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 답변 처리 및 조건 판정
    - 답변을 user_slots에 저장
    - 가능한 경우 룰베이스로 PASS/FAIL/UNKNOWN 판정
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

        # _judge_with_slot이 UNKNOWN이면, 답변이 들어왔으니 최소 PASS로 두지 말고 UNKNOWN 유지
        # 단, 답변 자체를 reason에 남겨 추후 판단 가능하게 함
        if status == "UNKNOWN":
            current_condition["status"] = "UNKNOWN"
            current_condition["reason"] = f"{reason or '추가 확인 필요'} | 사용자 답변: {user_answer}"
        else:
            current_condition["status"] = status
            current_condition["reason"] = reason or f"사용자 답변 반영: {user_answer}"

        conditions[current_index] = current_condition

        logger.info(
            "Answer processed",
            extra={
                "condition_index": current_index,
                "condition_type": ctype,
                "status": current_condition.get("status"),
            },
        )

        return {
            **state,
            "conditions": conditions,
            "user_slots": user_slots,
            "current_condition_index": current_index + 1,
            "user_answer": "",
        }

    except Exception as e:
        logger.error(
            "Error in process_answer_node",
            extra={"error": str(e)},
            exc_info=True,
        )
        return state


# =========================================================
# 7) Node: final_decision_node (최종 자격 판정)
# =========================================================
@trace_workflow(name="final_decision", tags=["eligibility", "decision"])
def final_decision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    최종 자격 판정
    - FAIL 하나라도 있으면 NOT_ELIGIBLE
    - UNKNOWN 남아있거나 extra_requirements 존재하면 PARTIALLY
    - 모두 PASS면 ELIGIBLE
    """
    try:
        conditions = state.get("conditions", []) or []
        extra_requirements = state.get("extra_requirements", None)

        if not conditions:
            return {
                **state,
                "final_result": "NOT_ELIGIBLE",
                "reason": "확인할 조건이 없습니다.",
            }

        pass_count = sum(1 for c in conditions if c.get("status") == "PASS")
        fail_count = sum(1 for c in conditions if c.get("status") == "FAIL")
        unknown_count = sum(1 for c in conditions if c.get("status") == "UNKNOWN")

        if fail_count > 0:
            final_result = "NOT_ELIGIBLE"
            reason = f"{fail_count}개 조건을 만족하지 못합니다."
        else:
            # extra_requirements가 있으면 시스템 자동판정 불가한 항목이 있다는 뜻 -> PARTIALLY
            if unknown_count > 0 or (extra_requirements not in (None, "", "null")):
                final_result = "PARTIALLY"
                msg = []
                if unknown_count > 0:
                    msg.append(f"{unknown_count}개 조건은 추가 확인이 필요합니다.")
                if extra_requirements not in (None, "", "null"):
                    msg.append("공고문 확인이 필요한 추가 요구사항이 있습니다.")
                reason = " ".join(msg) if msg else "추가 확인이 필요합니다."
            else:
                final_result = "ELIGIBLE"
                reason = "모든 자격 조건을 충족합니다."

        logger.info(
            "Final decision made",
            extra={
                "result": final_result,
                "pass": pass_count,
                "fail": fail_count,
                "unknown": unknown_count,
                "has_extra_requirements": bool(extra_requirements),
            },
        )

        return {
            **state,
            "final_result": final_result,
            "reason": reason,
        }

    except Exception as e:
        logger.error(
            "Error in final_decision_node",
            extra={"error": str(e)},
            exc_info=True,
        )
        return {
            **state,
            "final_result": "NOT_ELIGIBLE",
            "reason": f"판정 중 오류 발생: {str(e)}",
            "error": str(e),
        }