"""
Query Understanding Node
LLM을 사용하여 사용자 쿼리를 분석하고 의도, 키워드, 필터를 추출
"""

import json
from typing import Dict, Any
from pathlib import Path
from jinja2 import Template

from ....config.logger import get_logger
from ....observability import trace_llm_call, get_feature_tags
from ....llm import get_openai_client

logger = get_logger()


@trace_llm_call(
    name="query_understanding",
    tags=["node", "search", "llm", "query-analysis"]
)
def query_understanding_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 쿼리를 LLM으로 분석하여 의도, 키워드, 필터 추출

    분석 항목:
    - intent: 검색 의도 (policy_search, latest_policy, condition_search, specific_info)
    - keywords: 검색 키워드 리스트
    - filters: 필터 조건 (region, category, target_group)
    - sort_preference: 정렬 선호 (latest, relevance, budget_desc, deadline)
    - time_context: 시간 관련 컨텍스트

    Args:
        state: 현재 상태 (original_query 필수)

    Returns:
        Dict: 업데이트된 상태 (parsed_query 추가)
    """
    try:
        original_query = state.get("original_query", "")

        if not original_query:
            logger.warning("No query provided for understanding")
            return {
                **state,
                "parsed_query": {
                    "intent": "policy_search",
                    "keywords": [],
                    "filters": {
                        "region": None,
                        "category": None,
                        "target_group": None
                    },
                    "sort_preference": "relevance",
                    "time_context": None
                }
            }

        # Load Jinja2 template
        prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "search_query_understanding.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())

        # Render prompt
        prompt = template.render(query=original_query)

        # Call LLM
        llm_client = get_openai_client()
        response = llm_client.generate_with_system(
            system_prompt="당신은 정책 검색 쿼리 분석 전문가입니다. 반드시 유효한 JSON만 응답하세요.",
            user_message=prompt,
            temperature=0.0
        )

        # Parse JSON response
        try:
            # Clean response (remove markdown code blocks if present)
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()

            parsed_query = json.loads(clean_response)

            # Validate and set defaults
            parsed_query.setdefault("intent", "policy_search")
            parsed_query.setdefault("keywords", [])
            parsed_query.setdefault("filters", {})
            parsed_query["filters"].setdefault("region", None)
            parsed_query["filters"].setdefault("category", None)
            parsed_query["filters"].setdefault("target_group", None)
            parsed_query.setdefault("sort_preference", "relevance")
            parsed_query.setdefault("time_context", None)

        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse LLM response as JSON, using fallback",
                extra={"error": str(e), "response": response[:200]}
            )
            # Fallback: 기본 키워드 추출
            parsed_query = {
                "intent": "policy_search",
                "keywords": original_query.split(),
                "filters": {
                    "region": None,
                    "category": None,
                    "target_group": None
                },
                "sort_preference": "relevance",
                "time_context": None
            }

            # 간단한 키워드 기반 필터 추출
            query_lower = original_query.lower()

            # 최신 관련 키워드
            if any(kw in query_lower for kw in ["최신", "새로운", "최근"]):
                parsed_query["sort_preference"] = "latest"
                parsed_query["intent"] = "latest_policy"

            # 지역 추출
            regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종", "전국"]
            for region in regions:
                if region in original_query:
                    parsed_query["filters"]["region"] = region
                    break

            # 대상 그룹 추출
            target_groups = ["프리랜서", "청년", "중소기업", "예비창업자", "스타트업", "소상공인"]
            for group in target_groups:
                if group in original_query:
                    parsed_query["filters"]["target_group"] = group
                    break

        logger.info(
            "Query understanding completed",
            extra={
                "original_query": original_query,
                "intent": parsed_query.get("intent"),
                "keywords_count": len(parsed_query.get("keywords", [])),
                "has_region_filter": parsed_query.get("filters", {}).get("region") is not None,
                "sort_preference": parsed_query.get("sort_preference")
            }
        )

        return {
            **state,
            "parsed_query": parsed_query
        }

    except Exception as e:
        logger.error(
            "Error in query_understanding_node",
            extra={"error": str(e)},
            exc_info=True
        )
        # 에러 시에도 기본 parsed_query 반환
        return {
            **state,
            "parsed_query": {
                "intent": "policy_search",
                "keywords": state.get("original_query", "").split(),
                "filters": {
                    "region": None,
                    "category": None,
                    "target_group": None
                },
                "sort_preference": "relevance",
                "time_context": None
            },
            "error": str(e)
        }
