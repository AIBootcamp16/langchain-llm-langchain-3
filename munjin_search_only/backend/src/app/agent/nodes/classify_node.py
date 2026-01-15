"""
Classify Query Node
사용자 질문을 분석하여 웹 검색 필요 여부 판단
"""

from typing import Dict, Any
from ...config.logger import get_logger
from ...observability import trace_workflow

logger = get_logger()


@trace_workflow(name="classify_query", tags=["node", "classify"])
def classify_query_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 질문 분류
    
    웹 검색이 필요한 질문:
    - "최신", "링크", "홈페이지", "신청 방법", "접수" 등의 키워드 포함
    - 외부 정보가 필요한 질문
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태
    """
    try:
        current_query = state.get("current_query", "")
        
        # 웹 검색 트리거 키워드
        web_search_keywords = [
            "최신", "링크", "홈페이지", "신청 방법", "접수", 
            "url", "사이트", "웹사이트", "온라인", "신청서",
            "다운로드", "양식", "공고문"
        ]
        
        # 키워드 기반 판단
        need_web_search = any(
            keyword in current_query for keyword in web_search_keywords
        )
        
        logger.info(
            "Query classified",
            extra={
                "query": current_query,
                "need_web_search": need_web_search
            }
        )
        
        return {
            **state,
            "need_web_search": need_web_search
        }
        
    except Exception as e:
        logger.error(
            "Error in classify_query_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "need_web_search": False,
            "error": str(e)
        }

