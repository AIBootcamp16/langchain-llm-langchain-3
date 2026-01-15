"""
Retrieve Node
Qdrant + MySQL에서 관련 문서 검색
"""

from typing import Dict, Any, List
from ...config.logger import get_logger
from ...observability import trace_retrieval
from ...vector_store import get_qdrant_manager, get_embedder
from ...db.engine import get_db
from ...db.models import Policy, Document

logger = get_logger()


@trace_retrieval(
    name="retrieve_from_db",
    tags=["node", "retrieval", "qdrant"]
)
def retrieve_from_db_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    DB에서 관련 문서 검색
    
    Qdrant 벡터 검색으로 관련 문서 청크 조회
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (retrieved_docs 추가)
    """
    try:
        current_query = state.get("current_query", "")
        policy_id = state.get("policy_id")
        
        if not current_query:
            logger.warning("No query provided for retrieval")
            return {
                **state,
                "retrieved_docs": []
            }
        
        # Generate query embedding
        embedder = get_embedder()
        query_vector = embedder.embed_text(current_query)
        
        # Search in Qdrant with policy filter
        qdrant_manager = get_qdrant_manager()
        results = qdrant_manager.search(
            query_vector=query_vector,
            limit=5,
            score_threshold=0.7,
            filter_dict={"policy_id": policy_id} if policy_id else None
        )
        
        # Format retrieved documents
        retrieved_docs = []
        for result in results:
            payload = result.get("payload", {})
            retrieved_docs.append({
                "content": payload.get("content", ""),
                "score": result.get("score", 0.0),
                "doc_type": payload.get("doc_type", ""),
                "policy_id": payload.get("policy_id"),
                "chunk_index": payload.get("chunk_index", 0)
            })
        
        logger.info(
            "Documents retrieved",
            extra={
                "query": current_query,
                "results_count": len(retrieved_docs)
            }
        )
        
        return {
            **state,
            "retrieved_docs": retrieved_docs
        }
        
    except Exception as e:
        logger.error(
            "Error in retrieve_from_db_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "retrieved_docs": [],
            "error": str(e)
        }