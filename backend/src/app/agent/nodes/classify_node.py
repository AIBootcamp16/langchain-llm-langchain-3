"""
Classify Query Node
사용자 질문 유형 분류 (WEB_ONLY vs POLICY_QA)
"""

from typing import Dict, Any
from ...config.logger import get_logger
from ...observability import trace_workflow

logger = get_logger()


@trace_workflow(name="classify_query_type", tags=["node", "classify"])
def classify_query_type_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 질문 유형 분류: WEB_ONLY vs POLICY_QA
    
    WEB_ONLY (링크/홈페이지 요청):
    - "링크 알려줘", "홈페이지", "어디서 신청", "신청 방법"
    - 키워드: 링크, URL, 홈페이지, 사이트, 신청서 다운로드
    
    POLICY_QA (정책 내용 질문):
    - "지원 금액은?", "신청 대상은?", "조건은?"
    - 정책 내용에 대한 실제 질문
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (query_type 포함)
    """
    try:
        current_query = state.get("current_query", "").lower()
        
        # WEB_ONLY 트리거 키워드
        web_only_keywords = [
            "링크", "url", "홈페이지", "사이트", "웹사이트",
            "어디서 신청", "신청 방법", "신청하는 방법",
            "신청서 다운로드", "양식 다운로드", 
            "접수", "접수처", "공고문"
        ]
        
        # 키워드 기반 판단
        is_web_only = any(
            keyword in current_query for keyword in web_only_keywords
        )
        
        query_type = "WEB_ONLY" if is_web_only else "POLICY_QA"
        
        logger.info(
            "Query type classified",
            extra={
                "query": current_query,
                "query_type": query_type
            }
        )
        
        return {
            **state,
            "query_type": query_type,
            "need_web_search": False  # 기본값 (추후 check_sufficiency에서 결정)
        }
        
    except Exception as e:
        logger.error(
            "Error in classify_query_type_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "query_type": "POLICY_QA",  # 에러 시 기본값
            "need_web_search": False,
            "error": str(e)
        }


# 하위 호환성을 위해 기존 함수명도 유지
classify_query_node = classify_query_type_node

