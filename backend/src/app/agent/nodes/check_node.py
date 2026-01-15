"""
Check Sufficiency Node
검색된 문서의 충분성 판단
"""

from typing import Dict, Any
from ...config.logger import get_logger
from ...observability import trace_workflow

logger = get_logger()


@trace_workflow(name="check_sufficiency", tags=["node", "check"])
def check_sufficiency_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색된 문서의 충분성 판단
    
    판단 기준:
    1. 검색된 문서가 2개 이상
    2. 평균 스코어가 0.75 이상
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태
    """
    try:
        retrieved_docs = state.get("retrieved_docs", [])
        need_web_search = state.get("need_web_search", False)
        context_type = state.get("context_type", "policy")  # "policy" or "web"
        
        # Already flagged for web search
        if need_web_search:
            logger.info("Web search already flagged by classifier")
            return state
        
        # 웹 컨텍스트인 경우 1개 문서만 있어도 충분
        if context_type == "web":
            if len(retrieved_docs) >= 1:
                logger.info(
                    "Web context documents sufficient",
                    extra={"count": len(retrieved_docs), "context_type": "web"}
                )
                return {
                    **state,
                    "need_web_search": False
                }
        
        # Check document count (정책 문서의 경우)
        if len(retrieved_docs) < 2:
            logger.info(
                "Insufficient documents retrieved",
                extra={"count": len(retrieved_docs)}
            )
            return {
                **state,
                "need_web_search": True
            }
        
        # Check average score
        avg_score = sum(doc.get("score", 0.0) for doc in retrieved_docs) / len(retrieved_docs)
        
        if avg_score < 0.75:
            logger.info(
                "Low average score",
                extra={"avg_score": avg_score}
            )
            return {
                **state,
                "need_web_search": True
            }
        
        logger.info(
            "Documents sufficient",
            extra={
                "count": len(retrieved_docs),
                "avg_score": avg_score
            }
        )
        
        return {
            **state,
            "need_web_search": False
        }
        
    except Exception as e:
        logger.error(
            "Error in check_sufficiency_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "need_web_search": False,
            "error": str(e)
        }

