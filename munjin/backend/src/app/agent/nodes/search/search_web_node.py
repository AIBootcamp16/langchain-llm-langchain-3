"""
Search Web Search Node
Tavily를 이용한 웹 검색 (DuckDuckGo 폴백)
"""

from typing import Dict, Any, List
from datetime import date

from ....config.logger import get_logger
from ....config import get_settings
from ....observability import trace_tool, get_feature_tags
from ....web_search.clients.tavily_client import get_tavily_client

logger = get_logger()
settings = get_settings()


@trace_tool(
    name="search_web_search",
    tags=["node", "search", "web-search", "tavily"]
)
def search_web_search_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    웹 검색을 통한 추가 정보 수집

    검색 전략:
    1. 원본 쿼리 + "정부 지원" 키워드로 검색
    2. Tavily API 우선 사용 (고품질)
    3. DuckDuckGo 폴백 (무료)

    Args:
        state: 현재 상태 (original_query, parsed_query 필수)

    Returns:
        Dict: 업데이트된 상태 (web_sources 추가)
    """
    try:
        original_query = state.get("original_query", "")
        parsed_query = state.get("parsed_query", {})

        if not original_query:
            logger.warning("No query provided for web search")
            return {
                **state,
                "web_sources": []
            }

        # Build enhanced search query
        keywords = parsed_query.get("keywords", [])
        filters = parsed_query.get("filters", {})

        # Construct search query with context
        search_parts = []

        # Add keywords
        if keywords:
            search_parts.extend(keywords[:3])  # Top 3 keywords
        else:
            search_parts.append(original_query)

        # Add filter context
        if filters.get("region") and filters["region"] != "전국":
            search_parts.append(filters["region"])
        if filters.get("target_group"):
            search_parts.append(filters["target_group"])

        # Add policy context
        search_parts.append("정부 지원 사업")

        search_query = " ".join(search_parts)

        web_sources = []

        # Try Tavily first (if API key available)
        if settings.tavily_api_key:
            try:
                tavily_client = get_tavily_client()
                results = tavily_client.search(
                    query=search_query,
                    max_results=5,
                    search_depth="advanced"
                )

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
                        "query": search_query,
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

            with DDGS() as ddgs:
                results = list(ddgs.text(
                    search_query,
                    max_results=5
                ))

            for result in results:
                web_sources.append({
                    "url": result.get("href", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "score": 0.5,  # DuckDuckGo doesn't provide scores
                    "fetched_date": date.today().isoformat(),
                    "source_type": "duckduckgo"
                })

            logger.info(
                "DuckDuckGo web search completed",
                extra={
                    "query": search_query,
                    "results_count": len(web_sources)
                }
            )

            return {
                **state,
                "web_sources": web_sources
            }

        except ImportError:
            logger.warning("DuckDuckGo search not available (package not installed)")
            return {
                **state,
                "web_sources": []
            }
        except Exception as e:
            logger.error(
                "DuckDuckGo search failed",
                extra={"error": str(e)}
            )
            return {
                **state,
                "web_sources": []
            }

    except Exception as e:
        logger.error(
            "Error in search_web_search_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "web_sources": [],
            "error": str(e)
        }
