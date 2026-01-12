"""
Qdrant 클라이언트
벡터 DB 연결 및 관리
"""

from typing import List, Dict, Any, Optional
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchRequest,
)

from ..config import get_settings
from ..config.logger import get_logger

logger = get_logger()
settings = get_settings()


class QdrantManager:
    """
    Qdrant 벡터 DB 관리 클래스
    
    Attributes:
        client: Qdrant 클라이언트
        collection_name: 컬렉션 이름
    """
    
    def __init__(self):
        """Initialize Qdrant client"""
        try:
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=60
            )
            self.collection_name = settings.qdrant_collection
            
            logger.info(
                "Qdrant client initialized",
                extra={
                    "url": settings.qdrant_url,
                    "collection": self.collection_name
                }
            )
        except Exception as e:
            logger.error(
                "Failed to initialize Qdrant client",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def create_collection(
        self,
        vector_size: int = 1024,
        distance: Distance = Distance.COSINE,
        force_recreate: bool = False
    ) -> bool:
        """
        컬렉션 생성
        
        Args:
            vector_size: 벡터 차원 (bge-m3는 1024)
            distance: 거리 메트릭 (COSINE, EUCLID, DOT)
            force_recreate: 기존 컬렉션 삭제 후 재생성
        
        Returns:
            bool: 성공 여부
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_exists = any(
                col.name == self.collection_name for col in collections
            )
            
            if collection_exists:
                if force_recreate:
                    logger.warning(
                        "Deleting existing collection",
                        extra={"collection": self.collection_name}
                    )
                    self.client.delete_collection(self.collection_name)
                else:
                    logger.info(
                        "Collection already exists",
                        extra={"collection": self.collection_name}
                    )
                    return True
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance
                )
            )
            
            logger.info(
                "Collection created successfully",
                extra={
                    "collection": self.collection_name,
                    "vector_size": vector_size,
                    "distance": distance
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error creating collection",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def upsert_points(
        self,
        points: List[PointStruct]
    ) -> bool:
        """
        포인트 업서트 (생성 또는 업데이트)
        
        Args:
            points: 포인트 리스트
        
        Returns:
            bool: 성공 여부
        """
        try:
            if not points:
                logger.warning("No points to upsert")
                return False
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(
                "Points upserted successfully",
                extra={"count": len(points)}
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error upserting points",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        벡터 검색
        
        Args:
            query_vector: 쿼리 벡터
            limit: 반환 개수
            score_threshold: 최소 스코어 (선택)
            filter_dict: 필터 조건 (선택) 예: {"policy_id": 1}
        
        Returns:
            List[Dict]: 검색 결과 리스트
        """
        try:
            # Build filter
            query_filter = None
            if filter_dict:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filter_dict.items()
                ]
                query_filter = Filter(must=conditions)
            
            # Search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })
            
            logger.debug(
                "Search completed",
                extra={"results_count": len(formatted_results)}
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(
                "Error searching vectors",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def delete_points(
        self,
        point_ids: List[int]
    ) -> bool:
        """
        포인트 삭제
        
        Args:
            point_ids: 삭제할 포인트 ID 리스트
        
        Returns:
            bool: 성공 여부
        """
        try:
            if not point_ids:
                return False
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=point_ids
            )
            
            logger.info(
                "Points deleted successfully",
                extra={"count": len(point_ids)}
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Error deleting points",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        컬렉션 정보 조회
        
        Returns:
            Dict: 컬렉션 정보
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": info.name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(
                "Error getting collection info",
                extra={"error": str(e)},
                exc_info=True
            )
            raise


@lru_cache()
def get_qdrant_manager() -> QdrantManager:
    """
    Get cached Qdrant manager instance
    
    Returns:
        QdrantManager: Cached manager instance
    """
    return QdrantManager()

