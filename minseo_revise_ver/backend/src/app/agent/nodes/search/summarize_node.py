"""
Summarize Results Node
LLM을 사용하여 검색 결과를 요약
"""

from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Template

from ....config.logger import get_logger
from ....observability import trace_llm_call, get_feature_tags
from ....llm import get_llm_client

logger = get_logger()


@trace_llm_call(
    name="summarize_results",
    tags=["node", "search", "llm", "summarize"]
)
def summarize_results_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색 결과를 LLM으로 요약하고 최종 정책 리스트 구성

    Args:
        state: 현재 상태 (retrieved_docs, web_sources, parsed_query 필수)

    Returns:
        Dict: 업데이트된 상태 (summary, policies, total_count 추가)
    """
    try:
        original_query = state.get("original_query", "")
        parsed_query = state.get("parsed_query", {})
        retrieved_docs = state.get("retrieved_docs", [])
        web_sources = state.get("web_sources", [])

        # Build final policies list
        policies = []
        for doc in retrieved_docs:
            policy = {
                "id": doc.get("policy_id"),
                "program_id": doc.get("policy_id"),
                "program_name": doc.get("program_name"),
                "program_overview": doc.get("program_overview"),
                "region": doc.get("region"),
                "category": doc.get("category"),
                "support_description": doc.get("support_description"),
                "support_budget": doc.get("support_budget"),
                "apply_target": doc.get("apply_target"),
                "announcement_date": doc.get("announcement_date"),
                "application_method": doc.get("application_method"),
                "score": doc.get("score"),
                "source_type": "internal"
            }
            policies.append(policy)

        # Add web sources as supplementary results
        for idx, source in enumerate(web_sources):
            web_policy = {
                "id": -1000 - idx,  # Negative ID for web results
                "program_id": -1,
                "program_name": source.get("title", "웹 검색 결과"),
                "program_overview": source.get("snippet", ""),
                "region": "웹 검색",
                "category": "웹 검색 결과",
                "support_description": f"출처: {source.get('url', '')}",
                "support_budget": None,
                "apply_target": "웹 검색 결과 - 자세한 내용은 출처 링크를 확인하세요",
                "announcement_date": source.get("fetched_date"),
                "application_method": source.get("url"),
                "score": source.get("score", 0.5),
                "source_type": "web",
                "url": source.get("url")
            }
            policies.append(web_policy)

        total_count = len(policies)

        # Generate summary using LLM
        summary = _generate_summary(
            original_query=original_query,
            parsed_query=parsed_query,
            retrieved_docs=retrieved_docs,
            web_sources=web_sources,
            total_count=total_count
        )

        logger.info(
            "Summarize results completed",
            extra={
                "total_policies": len(policies),
                "internal_count": len(retrieved_docs),
                "web_count": len(web_sources),
                "summary_length": len(summary)
            }
        )

        return {
            **state,
            "summary": summary,
            "policies": policies,
            "total_count": total_count
        }

    except Exception as e:
        logger.error(
            "Error in summarize_results_node",
            extra={"error": str(e)},
            exc_info=True
        )
        # 에러 시에도 기본 결과 반환
        retrieved_docs = state.get("retrieved_docs", [])
        policies = [
            {
                "id": doc.get("policy_id"),
                "program_id": doc.get("policy_id"),
                "program_name": doc.get("program_name"),
                "region": doc.get("region"),
                "category": doc.get("category"),
                "score": doc.get("score"),
                "source_type": "internal"
            }
            for doc in retrieved_docs
        ]

        return {
            **state,
            "summary": f"검색 결과 {len(policies)}건을 찾았습니다.",
            "policies": policies,
            "total_count": len(policies),
            "error": str(e)
        }


def _generate_summary(
    original_query: str,
    parsed_query: Dict[str, Any],
    retrieved_docs: List[Dict[str, Any]],
    web_sources: List[Dict[str, Any]],
    total_count: int
) -> str:
    """
    LLM을 사용하여 검색 결과 요약 생성

    Args:
        original_query: 원본 쿼리
        parsed_query: 분석된 쿼리
        retrieved_docs: 검색된 문서
        web_sources: 웹 검색 결과
        total_count: 전체 결과 수

    Returns:
        str: 요약 텍스트
    """
    try:
        # 결과가 없는 경우
        if not retrieved_docs and not web_sources:
            return f"'{original_query}'에 대한 검색 결과가 없습니다. 검색어를 변경하거나 필터 조건을 조정해 보세요."

        # Load Jinja2 template
        prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "search_summarize_results.jinja2"

        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())

        # Render prompt
        prompt = template.render(
            original_query=original_query,
            parsed_query=parsed_query,
            retrieved_docs=retrieved_docs,
            web_sources=web_sources,
            total_count=total_count
        )

        # Call LLM
        llm_client = get_llm_client()
        summary = llm_client.generate_with_system(
            system_prompt="당신은 정책 검색 결과를 간결하게 요약하는 전문가입니다. 2-3문장으로 핵심만 요약하세요.",
            user_message=prompt,
            temperature=0.3
        )

        return summary.strip()

    except Exception as e:
        logger.warning(
            "Failed to generate LLM summary, using fallback",
            extra={"error": str(e)}
        )
        # Fallback summary
        internal_count = len(retrieved_docs)
        web_count = len(web_sources)

        if internal_count > 0:
            top_policy = retrieved_docs[0].get("program_name", "정책")
            top_score = retrieved_docs[0].get("score", 0)

            summary_parts = [
                f"'{original_query}' 검색 결과 총 {total_count}건을 찾았습니다."
            ]

            if top_score >= 0.7:
                summary_parts.append(f"'{top_policy}'이(가) 가장 관련도가 높습니다(유사도: {top_score:.0%}).")
            else:
                summary_parts.append(f"상위 결과로 '{top_policy}'이(가) 검색되었습니다.")

            if web_count > 0:
                summary_parts.append(f"웹 검색을 통해 {web_count}건의 추가 정보를 확인했습니다.")

            return " ".join(summary_parts)
        elif web_count > 0:
            return f"내부 데이터베이스에서 관련 정책을 찾지 못해 웹 검색 결과 {web_count}건을 제공합니다."
        else:
            return f"'{original_query}'에 대한 검색 결과가 없습니다."
