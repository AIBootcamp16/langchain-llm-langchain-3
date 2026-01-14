"""
Policy Document Cache
정책 문서 캐시 관리 (메모리 기반)
"""

from typing import Dict, Optional, Any, List
from datetime import datetime, timedelta
import threading

from ..config.logger import get_logger

logger = get_logger()


class PolicyCache:
    """
    정책 문서 캐시 (메모리)
    
    공고 선택 시 전체 문서를 캐시에 저장하여
    매번 Qdrant 벡터 검색을 하지 않고 재사용
    """
    
    TTL_SECONDS = 86400  # 24시간 (백업용)
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def set_policy_context(
        self,
        session_id: str,
        policy_id: int,
        policy_info: Dict[str, Any],
        documents: List[Dict[str, Any]]
    ):
        """
        공고 선택 시 전체 문서 캐시에 저장
        
        Args:
            session_id: 세션 ID
            policy_id: 정책 ID
            policy_info: 정책 기본 정보
            documents: 전체 문서 청크 리스트
        """
        with self._lock:
            self._cache[session_id] = {
                "policy_id": policy_id,
                "policy_info": policy_info,
                "documents": documents,
                "cached_at": datetime.now().isoformat()
            }
            self._timestamps[session_id] = datetime.now()
            
            logger.info(
                "Policy context cached",
                extra={
                    "session_id": session_id,
                    "policy_id": policy_id,
                    "documents_count": len(documents)
                }
            )
    
    def get_policy_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        캐시된 정책 문서 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            Optional[Dict]: 정책 컨텍스트 (policy_id, policy_info, documents 포함)
                          캐시 미스 시 None
        """
        with self._lock:
            # TTL 체크
            if session_id in self._timestamps:
                if datetime.now() - self._timestamps[session_id] > timedelta(seconds=self.TTL_SECONDS):
                    # TTL 초과 시 삭제
                    logger.info(
                        "Policy context expired",
                        extra={"session_id": session_id}
                    )
                    self._cache.pop(session_id, None)
                    self._timestamps.pop(session_id, None)
                    return None
            
            context = self._cache.get(session_id)
            
            if context:
                logger.debug(
                    "Policy context cache hit",
                    extra={
                        "session_id": session_id,
                        "policy_id": context.get("policy_id")
                    }
                )
            else:
                logger.debug(
                    "Policy context cache miss",
                    extra={"session_id": session_id}
                )
            
            return context.copy() if context else None
    
    def clear_policy_context(self, session_id: str):
        """
        정책 문서 캐시 제거 (대화창 나갈 때 호출)
        
        Args:
            session_id: 세션 ID
        """
        with self._lock:
            if session_id in self._cache:
                policy_id = self._cache[session_id].get("policy_id")
                self._cache.pop(session_id, None)
                self._timestamps.pop(session_id, None)
                
                logger.info(
                    "Policy context cleared",
                    extra={
                        "session_id": session_id,
                        "policy_id": policy_id
                    }
                )
    
    def set_ttl(self, session_id: str, seconds: int):
        """
        TTL 설정 (백업용)
        
        Args:
            session_id: 세션 ID
            seconds: TTL (초)
        """
        with self._lock:
            if session_id in self._timestamps:
                # TTL 커스텀 설정은 현재 구현에서는 사용하지 않음
                # 필요 시 세션별 TTL을 저장하는 dict 추가 가능
                pass
    
    def get_all_sessions(self) -> List[str]:
        """
        모든 세션 ID 조회 (디버깅용)
        
        Returns:
            List[str]: 세션 ID 목록
        """
        with self._lock:
            return list(self._cache.keys())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        캐시 통계 조회 (모니터링용)
        
        Returns:
            Dict: 캐시 통계
        """
        with self._lock:
            total_sessions = len(self._cache)
            total_documents = sum(
                len(ctx.get("documents", []))
                for ctx in self._cache.values()
            )
            
            return {
                "total_sessions": total_sessions,
                "total_documents": total_documents,
                "avg_documents_per_session": (
                    total_documents / total_sessions if total_sessions > 0 else 0
                )
            }
    
    def clear_all(self):
        """
        모든 캐시 삭제 (테스트용)
        """
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("All policy contexts cleared")


# 싱글톤 인스턴스
_policy_cache_instance: Optional[PolicyCache] = None
_policy_cache_lock = threading.Lock()


def get_policy_cache() -> PolicyCache:
    """
    PolicyCache 싱글톤 인스턴스 반환
    
    Returns:
        PolicyCache: 캐시 인스턴스
    """
    global _policy_cache_instance
    
    if _policy_cache_instance is None:
        with _policy_cache_lock:
            if _policy_cache_instance is None:
                _policy_cache_instance = PolicyCache()
    
    return _policy_cache_instance

