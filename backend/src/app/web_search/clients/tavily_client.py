"""
Tavily Web Search Client
Tavily API를 사용한 웹 검색 클라이언트
"""

from typing import List, Dict, Any, Optional
from tavily import TavilyClient

from ...config import get_settings
from ...config.logger import get_logger
from ...observability import trace_tool

logger = get_logger()
settings = get_settings()


class TavilySearchClient:
    """
    Tavily 웹 검색 클라이언트
    
    Tavily는 LLM에 최적화된 웹 검색 API로,
    고품질의 관련성 높은 결과를 제공합니다.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client
        
        Args:
            api_key: Tavily API 키 (없으면 settings에서 가져옴)
        """
        self.api_key = api_key or settings.tavily_api_key
        if not self.api_key:
            logger.warning("Tavily API key not configured")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)
            logger.info("Tavily client initialized")
    
    @trace_tool(name="tavily_search", tags=["web_search", "tavily"])
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        days: int = 90  # 최근 90일 이내 결과만
    ) -> List[Dict[str, Any]]:
        """
        Tavily 웹 검색 실행
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            search_depth: 검색 깊이 ("basic" 또는 "advanced")
            include_domains: 포함할 도메인 리스트
            exclude_domains: 제외할 도메인 리스트
            days: 최근 N일 이내 결과만 (기본값: 90일)
        
        Returns:
            List[Dict]: 검색 결과 리스트
                - title: 제목
                - url: URL
                - content: 내용
                - score: 관련성 점수
                - published_date: 게시 날짜
        """
        if not self.client:
            logger.error("Tavily client not initialized")
            return []
        
        try:
            logger.info(
                "Executing Tavily search",
                extra={
                    "query": query,
                    "max_results": max_results,
                    "search_depth": search_depth,
                    "days_filter": days
                }
            )
            
            # Execute search
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                include_answer=True,  # Get AI-generated answer
                include_raw_content=False,  # Don't include full HTML
                days=days  # 최근 N일 이내 결과만
            )
            
            # Parse results
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0),
                    "published_date": item.get("published_date")
                })
            
            # Add AI answer if available
            ai_answer = response.get("answer")
            if ai_answer:
                logger.info(
                    "Tavily AI answer received",
                    extra={"answer_length": len(ai_answer)}
                )
            
            logger.info(
                "Tavily search completed",
                extra={
                    "query": query,
                    "results_count": len(results),
                    "has_ai_answer": bool(ai_answer)
                }
            )
            
            return results
            
        except Exception as e:
            logger.error(
                "Tavily search failed",
                extra={"query": query, "error": str(e)},
                exc_info=True
            )
            return []
    
    @trace_tool(name="tavily_qna_search", tags=["web_search", "tavily", "qna"])
    def qna_search(self, query: str) -> Optional[str]:
        """
        Tavily Q&A 검색 (직접 답변 반환)
        
        Args:
            query: 질문
        
        Returns:
            str: AI 생성 답변 (없으면 None)
        """
        if not self.client:
            logger.error("Tavily client not initialized")
            return None
        
        try:
            logger.info("Executing Tavily Q&A search", extra={"query": query})
            
            response = self.client.qna_search(query=query)
            
            logger.info(
                "Tavily Q&A search completed",
                extra={"query": query, "has_answer": bool(response)}
            )
            
            return response
            
        except Exception as e:
            logger.error(
                "Tavily Q&A search failed",
                extra={"query": query, "error": str(e)},
                exc_info=True
            )
            return None


# Singleton instance
_tavily_client: Optional[TavilySearchClient] = None


def get_tavily_client() -> TavilySearchClient:
    """
    Get Tavily client singleton
    
    Returns:
        TavilySearchClient: Tavily 클라이언트 인스턴스
    """
    global _tavily_client
    
    if _tavily_client is None:
        _tavily_client = TavilySearchClient()
    
    return _tavily_client

