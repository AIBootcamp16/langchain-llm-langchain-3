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


class EligibilityState(TypedDict, total=False):
    """
    자격 확인 워크플로우 상태 (Phase 4)

    total=False 로 두면:
    - LangGraph에서 "업데이트 dict는 최소 1개 키만 포함하면 됨"
    - 각 노드가 필요한 필드만 부분 업데이트 가능
    - 초기 state를 만들 때도 유연해짐
    """

    # ===== 필수로 쓰는 핵심 상태 =====
    session_id: str
    policy_id: int
    apply_target: str
    conditions: List[Dict[str, Any]]           # [{"name":..., "description":..., "status":...}, ...]
    user_slots: Dict[str, Any]                 # {"age": 25, "region": "서울", ...}
    current_question: str
    current_condition_index: int
    user_answer: str                           # 사용자 답변 (Q&A 방식)

    # ✅ 너 로그에 실제로 들어가던 값까지 포함
    final_result: Literal["ELIGIBLE", "NOT_ELIGIBLE", "PARTIALLY", "CANNOT_DETERMINE"]
    reason: str

    # ===== 에러/추가 요구사항 =====
    error: Optional[str]                       # 에러 메시지 저장
    extra_requirements: Optional[Any]          # LLM 추출의 "추가 요구사항" 등

    # ===== (로그에서 문제였던) 체크리스트 관련 =====
    checklist: List[Dict[str, Any]]            # 조건을 체크리스트 형태로 정리한 것
    checklist_result: List[Dict[str, Any]]     # 체크리스트 판정 결과

    # ===== 완료 플래그 =====
    completed: bool                            # 모든 조건 확인 완료 여부