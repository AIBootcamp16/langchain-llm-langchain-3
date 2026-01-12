"""
Text Chunking
텍스트를 벡터 검색에 적합한 크기로 분할
"""

from typing import List, Dict, Any
import re

from ..config import get_settings
from ..config.logger import get_logger

logger = get_logger()
settings = get_settings()


class TextChunker:
    """
    텍스트 청킹 클래스
    
    Attributes:
        chunk_size: 청크 크기 (문자 수)
        chunk_overlap: 청크 겹침 (문자 수)
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize chunker
        
        Args:
            chunk_size: 청크 크기 (기본값: settings.chunk_size)
            chunk_overlap: 청크 겹침 (기본값: settings.chunk_overlap)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        logger.debug(
            "Text chunker initialized",
            extra={
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
        )
    
    def split_text(
        self,
        text: str,
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 분할할 텍스트
            metadata: 메타데이터 (각 청크에 포함됨)
        
        Returns:
            List[Dict]: 청크 리스트 (content, metadata 포함)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # Split into sentences first (한국어 문장 분리)
        sentences = self._split_into_sentences(text)
        
        # Combine sentences into chunks
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence exceeds chunk_size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": metadata or {},
                    "chunk_index": len(chunks)
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk)
                current_chunk = overlap_text + " " + sentence
                current_length = len(current_chunk)
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_length += sentence_length
        
        # Add last chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": metadata or {},
                "chunk_index": len(chunks)
            })
        
        logger.debug(
            "Text chunked",
            extra={
                "original_length": len(text),
                "num_chunks": len(chunks)
            }
        )
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        텍스트 정제
        
        Args:
            text: 원본 텍스트
        
        Returns:
            str: 정제된 텍스트
        """
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove multiple newlines
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        텍스트를 문장으로 분리 (한국어 지원)
        
        Args:
            text: 원본 텍스트
        
        Returns:
            List[str]: 문장 리스트
        """
        # 한국어 문장 종결 부호: . ! ? 。
        sentence_endings = r'[.!?。]'
        
        # Split by sentence endings
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _get_overlap_text(self, text: str) -> str:
        """
        청크 겹침 텍스트 추출
        
        Args:
            text: 원본 텍스트
        
        Returns:
            str: 겹침 텍스트
        """
        if len(text) <= self.chunk_overlap:
            return text
        
        # Get last chunk_overlap characters
        return text[-self.chunk_overlap:]


def chunk_text(
    text: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
    metadata: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    텍스트 청킹 헬퍼 함수
    
    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (선택)
        chunk_overlap: 청크 겹침 (선택)
        metadata: 메타데이터 (선택)
    
    Returns:
        List[Dict]: 청크 리스트
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.split_text(text, metadata=metadata)

