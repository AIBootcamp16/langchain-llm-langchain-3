"""
Web Search Node
DuckDuckGo/Tavily로 웹 검색 수행
"""

from typing import Dict, Any, List
from datetime import date, datetime
from ...config.logger import get_logger
from ...config import get_settings
from ...observability import trace_tool
from ...web_search.clients.tavily_client import get_tavily_client
from ...domain.policy import PolicyResponse

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


@trace_tool(name="policy_web_search", tags=["node", "search", "web"])
def policy_web_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search Agent용 웹 검색 (부족한 정책 정보 보완)
    """
    if not state.get("use_web_search"):
        return state
        
    try:
        query = state.get("query", "")
        tavily_client = get_tavily_client()
        
        # 웹 검색 실행
        web_results = tavily_client.search(
            query=f"{query} 정부 지원 사업 공고",
            max_results=5,
            search_depth="advanced"
        )
        
        # 웹 결과를 PolicyResponse 형태로 변환 (가상 정책)
        converted_results = []
        for idx, res in enumerate(web_results):
            policy = PolicyResponse(
                id=-1000 - idx, # 음수 ID
                program_id=-1,
                region="웹 검색",
                category="웹 검색 결과",
                program_name=res.get("title", "제목 없음"),
                program_overview=res.get("content", ""),
                support_description=f"출처: {res.get('url', '')}",
                support_budget=0,
                support_scale="웹 검색",
                supervising_ministry="웹 검색",
                apply_target="웹 검색 결과 - 자세한 내용은 출처 링크를 확인하세요",
                announcement_date=datetime.now().strftime("%Y-%m-%d"),
                biz_process="",
                application_method=f"링크 참조: {res.get('url', '')}",
                contact_agency=[res.get("url", "")],
                contact_number=[],
                required_documents=[],
                collected_date=datetime.now().strftime("%Y-%m-%d"),
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                score=res.get("score", 0.5)
            )
            converted_results.append(policy)
            
        return {**state, "policies": state.get("policies", []) + converted_results}
        
    except Exception as e:
        logger.error("Error in policy web search node", extra={"error": str(e)}, exc_info=True)
        return state
