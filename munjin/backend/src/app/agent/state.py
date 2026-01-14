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


class SearchState(TypedDict):
    """
    정책 검색 워크플로우 상태

    워크플로우:
    START → query_understanding → retrieve → check_sufficiency
                                                    ↓
                    summarize ← [충분] | [부족] → web_search → summarize → END

    Attributes:
        session_id: 세션 ID
        original_query: 원본 검색 쿼리

        # Query Understanding 결과 (LLM 분석)
        parsed_query: 분석된 쿼리 정보
            - intent: 검색 의도 (예: "최신 정책 조회", "조건 검색")
            - keywords: 추출된 키워드 리스트
            - filters: 추출된 필터 조건
                - region: 지역 필터 (예: "서울", "전국")
                - category: 카테고리 필터 (예: "사업화", "글로벌")
                - target_group: 대상 그룹 (예: "프리랜서", "청년")
            - sort_preference: 정렬 선호도 (예: "latest", "relevance")
            - time_context: 시간 관련 컨텍스트 (예: "최신", "2024년")

        # 검색 결과
        retrieved_docs: Qdrant + MySQL 검색 결과 리스트
            - policy_id: 정책 ID
            - program_name: 정책명
            - content: 매칭된 청크 내용
            - score: 유사도 점수
            - region: 지역
            - category: 카테고리
            - metadata: 추가 메타데이터

        # 충분성 검사 결과
        is_sufficient: 검색 결과 충분 여부
        sufficiency_reason: 충분성 판단 사유
        top_score: 최고 유사도 점수
        grader_result: LLM Grader 결과 (선택)

        # 웹 검색 결과 (필요시)
        web_sources: 웹 검색 결과 리스트
            - url: URL
            - title: 제목
            - snippet: 요약 내용
            - score: 점수
            - fetched_date: 조회일
            - source_type: 소스 타입 (tavily/duckduckgo)

        # 최종 결과
        summary: 요약된 검색 결과
        policies: 최종 정책 리스트 (PolicyResponse 형식)
        total_count: 전체 결과 수

        # 에러 핸들링
        error: 에러 메시지 (선택)
    """
    session_id: str
    original_query: str

    # Query Understanding
    parsed_query: Dict[str, Any]

    # Retrieved Documents
    retrieved_docs: List[Dict[str, Any]]

    # Sufficiency Check
    is_sufficient: bool
    sufficiency_reason: str
    top_score: float
    grader_result: Optional[Dict[str, Any]]

    # Web Search
    web_sources: List[Dict[str, Any]]

    # Final Results
    summary: str
    policies: List[Dict[str, Any]]
    total_count: int

    # Error
    error: Optional[str]
