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
        
        # Already flagged for web search
        if need_web_search:
            logger.info("Web search already flagged by classifier")
            return state
        
        # Check document count
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


@trace_workflow(name="check_policy_sufficiency", tags=["node", "search", "logic"])
def check_policy_sufficiency_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search Agent용 결과 충분성 판단
    Top-1 유사도가 기준치(0.65) 이상인지 확인
    """
    score = state.get("sufficiency_score", 0.0)
    threshold = 0.65
    
    policies = state.get("policies", [])
    
    # 1. 결과가 없으면 -> 웹 검색 (Grader 불필요)
    if not policies:
        return {**state, "use_web_search": True, "run_grader": False}
    
    # 2. 점수가 기준치 이상이면 -> 충분함 (웹 검색 X, Grader X)
    if score >= threshold:
        return {**state, "use_web_search": False, "run_grader": False}
    
    # 3. 점수가 낮으면 -> LLM Grader로 정밀 검사 필요
    return {
        **state,
        "use_web_search": False, # Grader가 결정하도록 일단 False
        "run_grader": True
    }
