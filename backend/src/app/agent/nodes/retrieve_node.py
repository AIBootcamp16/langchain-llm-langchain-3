"""
Retrieve Node
캐시에서 정책 문서 조회 (Qdrant 벡터 검색 제거!)
"""

from typing import Dict, Any, List
from ...config.logger import get_logger
from ...observability import trace_retrieval
from ...cache import get_policy_cache

logger = get_logger()
policy_cache = get_policy_cache()


@trace_retrieval(
    name="load_cached_docs",
    tags=["node", "retrieval", "cache"]
)
def load_cached_docs_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    캐시에서 정책 문서 조회 (벡터 검색 없음!)
    
    공고 선택 시 이미 캐시에 저장된 전체 문서를 가져옴
    GPT-4가 전체 문서에서 의미 기반으로 관련 정보 찾음
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (retrieved_docs, policy_info 추가)
    """
    try:
        session_id = state.get("session_id")
        
        if not session_id:
            logger.error("No session_id provided")
            return {
                **state,
                "retrieved_docs": [],
                "policy_info": {},
                "error": "세션 ID가 없습니다."
            }
        
        # 캐시에서 정책 문서 조회
        policy_context = policy_cache.get_policy_context(session_id)
        
        if not policy_context:
            # 캐시 미스 시 에러
            error_msg = "정책 문서가 로드되지 않았습니다. 프론트엔드에서 /chat/init-policy를 먼저 호출하세요."
            logger.error(
                "Policy context cache miss",
                extra={"session_id": session_id}
            )
            return {
                **state,
                "retrieved_docs": [],
                "policy_info": {},
                "error": error_msg
            }
        
        # 캐시에서 문서 가져오기 (전체 문서!)
        documents = policy_context.get("documents", [])
        policy_info = policy_context.get("policy_info", {})
        
        # Format documents for LLM
        retrieved_docs = []
        for doc in documents:
            payload = doc.get("payload", {})
            retrieved_docs.append({
                "content": payload.get("content", ""),
                "doc_type": payload.get("doc_type", ""),
                "policy_id": payload.get("policy_id"),
                "chunk_index": payload.get("chunk_index", 0)
            })
        
        logger.info(
            "Documents loaded from cache",
            extra={
                "session_id": session_id,
                "documents_count": len(retrieved_docs),
                "policy_id": policy_context.get("policy_id")
            }
        )
        
        return {
            **state,
            "retrieved_docs": retrieved_docs,
            "policy_info": policy_info
        }
        
    except Exception as e:
        logger.error(
            "Error in load_cached_docs_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "retrieved_docs": [],
            "policy_info": {},
            "error": str(e)
        }


# 하위 호환성을 위해 기존 함수명도 유지
retrieve_from_db_node = load_cached_docs_node

