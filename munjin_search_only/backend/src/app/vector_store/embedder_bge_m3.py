"""
BGE-M3 Embedder
한국어 특화 임베딩 모델 (BAAI/bge-m3)
"""

from typing import List, Union
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from ..config import get_settings
from ..config.logger import get_logger

logger = get_logger()
settings = get_settings()


class BGEm3Embedder:
    """
    BGE-M3 임베딩 생성기
    
    Attributes:
        model: SentenceTransformer 모델
        model_name: 모델 이름
        dimension: 임베딩 차원
    """
    
    def __init__(self):
        """Initialize BGE-M3 model"""
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        
        try:
            logger.info(
                "Loading embedding model",
                extra={"model": self.model_name}
            )
            
            self.model = SentenceTransformer(
                self.model_name,
                device="cpu"  # GPU 사용 시 "cuda"로 변경
            )
            
            logger.info(
                "Embedding model loaded successfully",
                extra={
                    "model": self.model_name,
                    "dimension": self.dimension
                }
            )
            
        except Exception as e:
            logger.error(
                "Failed to load embedding model",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트 임베딩
        
        Args:
            text: 임베딩할 텍스트
        
        Returns:
            List[float]: 임베딩 벡터
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return [0.0] * self.dimension
            
            embedding = self.model.encode(
                text,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(
                "Error embedding text",
                extra={"error": str(e), "text_length": len(text)},
                exc_info=True
            )
            raise
    
    def embed_batch(
        self, 
        texts: List[str],
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        배치 텍스트 임베딩
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: 배치 크기
            show_progress: 진행률 표시 여부
        
        Returns:
            List[List[float]]: 임베딩 벡터 리스트
        """
        try:
            if not texts:
                logger.warning("Empty text list provided for embedding")
                return []
            
            # Filter empty texts
            filtered_texts = [text for text in texts if text and text.strip()]
            
            if not filtered_texts:
                logger.warning("All texts are empty after filtering")
                return [[0.0] * self.dimension] * len(texts)
            
            embeddings = self.model.encode(
                filtered_texts,
                batch_size=batch_size,
                normalize_embeddings=True,
                show_progress_bar=show_progress
            )
            
            logger.info(
                "Batch embedding completed",
                extra={"count": len(filtered_texts)}
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(
                "Error embedding batch",
                extra={"error": str(e), "batch_size": len(texts)},
                exc_info=True
            )
            raise
    
    def get_model_info(self) -> dict:
        """
        모델 정보 반환
        
        Returns:
            dict: 모델 정보
        """
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_seq_length": self.model.max_seq_length
        }


@lru_cache()
def get_embedder() -> BGEm3Embedder:
    """
    Get cached embedder instance
    
    Returns:
        BGEm3Embedder: Cached embedder instance
    """
    return BGEm3Embedder()

