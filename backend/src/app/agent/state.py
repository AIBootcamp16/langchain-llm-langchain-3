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


class EligibilityState(TypedDict):
    """
    자격 확인 워크플로우 상태 (Phase 4)
    
    Attributes:
        session_id: 세션 ID
        policy_id: 정책 ID
        apply_target: 신청 대상 텍스트
        conditions: 조건 리스트
        user_slots: 사용자 입력 슬롯
        current_question: 현재 질문
        current_condition_index: 현재 조건 인덱스
        final_result: 최종 결과
        reason: 판정 사유
    """
    session_id: str
    policy_id: int
    apply_target: str
    conditions: List[Dict[str, Any]]  # {"name": str, "description": str, "status": "UNKNOWN/PASS/FAIL"}
    user_slots: Dict[str, Any]  # {"age": 25, "region": "서울", ...}
    current_question: str
    current_condition_index: int
    final_result: Literal["ELIGIBLE", "NOT_ELIGIBLE", "PARTIALLY"]
    reason: str

