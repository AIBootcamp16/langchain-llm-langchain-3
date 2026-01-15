"""
Agent State Definitions
LangGraph 워크플로우 상태 정의
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal


class QAState(TypedDict):
    """
    Q&A 워크플로우 상태
    
    Attributes:
        session_id: 세션 ID
        policy_id: 정책 ID
        messages: 대화 이력
        current_query: 현재 질문
        retrieved_docs: 검색된 문서
        web_sources: 웹 검색 결과
        answer: 생성된 답변
        need_web_search: 웹 검색 필요 여부
        evidence: 근거 목록
        error: 에러 메시지 (선택)
    """
    session_id: str
    policy_id: int
    messages: List[Dict[str, str]]  # {"role": "user/assistant", "content": str}
    current_query: str
    retrieved_docs: List[Dict[str, Any]]
    web_sources: List[Dict[str, Any]]
    answer: str
    need_web_search: bool
    evidence: List[Dict[str, Any]]
    error: Optional[str]


# backend/src/app/agent/state.py

class EligibilityState(TypedDict):
    """
    자격 확인 워크플로우 상태 (Phase 4)
    """
    session_id: str
    policy_id: int
    apply_target: str  # 정책 신청 대상 원문 [cite: 31-32]
    conditions: List[Dict[str, Any]]  # 추출된 14대 조건 리스트 [cite: 34-37, 47-57]
    extra_requirements: Optional[str]  # [공고문 확인 요망] 항목들 [cite: 73, 77-79]
    
    # UI 체크리스트용 필드 추가 [cite: 192-193]
    checklist: List[Dict[str, Any]]  # UI에 보여줄 항목들
    checklist_result: List[Dict[str, Any]]  # UI에서 선택된 결과 (PASS/FAIL/UNKNOWN) [cite: 222-227]
    
    user_slots: Dict[str, Any]
    current_question: str
    current_condition_index: int
    
    # 판정 결과 리터럴 고도화 [cite: 40, 271-275]
    final_result: Literal["ELIGIBLE", "NOT_ELIGIBLE", "CANNOT_DETERMINE"]
    reason: str