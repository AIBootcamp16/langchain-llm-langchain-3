"""
Chat History Cache
대화 이력 캐시 관리 (메모리 기반)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import threading


class ChatCache:
    """
    대화 이력 캐시 (메모리)
    
    무제한 대화 이력 유지 (브라우저 탭 닫을 때까지)
    """
    
    MAX_HISTORY_TURNS = None  # 무제한 (None = 제한 없음)
    TTL_SECONDS = 86400       # 24시간 (백업용)
    
    def __init__(self):
        self._cache: Dict[str, List[Dict]] = {}
        self._timestamps: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """
        세션의 대화 이력 조회
        
        Args:
            session_id: 세션 ID
        
        Returns:
            List[Dict]: 대화 이력 (role, content 포함)
        """
        with self._lock:
            # TTL 체크
            if session_id in self._timestamps:
                if datetime.now() - self._timestamps[session_id] > timedelta(seconds=self.TTL_SECONDS):
                    # TTL 초과 시 삭제
                    self._cache.pop(session_id, None)
                    self._timestamps.pop(session_id, None)
                    return []
            
            return self._cache.get(session_id, []).copy()
    
    def add_message(self, session_id: str, role: str, content: str):
        """
        대화 메시지 추가
        
        무제한 메시지 저장 (세션 종료 시까지)
        
        Args:
            session_id: 세션 ID
            role: 메시지 역할 (user/assistant)
            content: 메시지 내용
        """
        with self._lock:
            if session_id not in self._cache:
                self._cache[session_id] = []
            
            # 메시지 추가
            self._cache[session_id].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            
            # 턴 제한 없음 (무제한 저장)
            # 브라우저 탭 닫을 때 cleanup API가 호출되어 자동 삭제
            
            # 타임스탬프 업데이트
            self._timestamps[session_id] = datetime.now()
    
    def clear_session(self, session_id: str):
        """
        세션의 대화 이력 삭제 (대화창 나갈 때 호출)
        
        Args:
            session_id: 세션 ID
        """
        with self._lock:
            self._cache.pop(session_id, None)
            self._timestamps.pop(session_id, None)
    
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
    
    def clear_all(self):
        """
        모든 캐시 삭제 (테스트용)
        """
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()


# 싱글톤 인스턴스
_chat_cache_instance: Optional[ChatCache] = None
_chat_cache_lock = threading.Lock()


def get_chat_cache() -> ChatCache:
    """
    ChatCache 싱글톤 인스턴스 반환
    
    Returns:
        ChatCache: 캐시 인스턴스
    """
    global _chat_cache_instance
    
    if _chat_cache_instance is None:
        with _chat_cache_lock:
            if _chat_cache_instance is None:
                _chat_cache_instance = ChatCache()
    
    return _chat_cache_instance

