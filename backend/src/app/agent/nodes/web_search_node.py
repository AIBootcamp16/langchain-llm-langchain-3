"""
Web Search Node
DuckDuckGo/Tavily로 웹 검색 수행
"""

from typing import Dict, Any, List
from datetime import date
from ...config.logger import get_logger
from ...config import get_settings
from ...observability import trace_tool
from ...web_search.clients.tavily_client import get_tavily_client

logger = get_logger()
settings = get_settings()


@trace_tool(name="web_search", tags=["node", "web-search"])
def web_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    웹 검색 수행 (Tavily 우선, DuckDuckGo 대체)
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (web_sources 추가)
    """
    try:
        current_query = state.get("current_query", "")
        policy_id = state.get("policy_id")
        
        if not current_query:
            logger.warning("No query provided for web search")
            return {
                **state,
                "web_sources": []
            }
        
        web_sources = []
        
        # Try Tavily first (if API key is available)
        if settings.tavily_api_key:
            try:
                tavily_client = get_tavily_client()
                results = tavily_client.search(
                    query=current_query,
                    max_results=5,
                    search_depth="advanced"
                )
                
                # Format Tavily results
                for result in results:
                    web_sources.append({
                        "url": result.get("url", ""),
                        "title": result.get("title", ""),
                        "snippet": result.get("content", ""),
                        "score": result.get("score", 0.0),
                        "fetched_date": date.today().isoformat(),
                        "source_type": "tavily"
                    })
                
                logger.info(
                    "Tavily web search completed",
                    extra={
                        "query": current_query,
                        "results_count": len(web_sources)
                    }
                )
                
                return {
                    **state,
                    "web_sources": web_sources
                }
                
            except Exception as e:
                logger.warning(
                    "Tavily search failed, falling back to DuckDuckGo",
                    extra={"error": str(e)}
                )
        
        # Fallback to DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            
            # Perform search
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    current_query,
                    max_results=3
                ))
            
            # Format web sources
            for result in results:
                web_sources.append({
                    "url": result.get("href", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "fetched_date": date.today().isoformat(),
                    "source_type": "duckduckgo"
                })
            
            logger.info(
                "DuckDuckGo web search completed",
                extra={
                    "query": current_query,
                    "results_count": len(web_sources)
                }
            )
            
            return {
                **state,
                "web_sources": web_sources
            }
            
        except ImportError:
            logger.warning("DuckDuckGo search not available")
            return {
                **state,
                "web_sources": []
            }
        
    except Exception as e:
        logger.error(
            "Error in web_search_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "web_sources": [],
            "error": str(e)
        }

