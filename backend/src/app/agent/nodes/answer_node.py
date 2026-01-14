"""
Answer Generation Nodes
LLM으로 최종 답변 생성 (3가지 노드)
"""

from typing import Dict, Any
from jinja2 import Template
from pathlib import Path

from ...config.logger import get_logger
from ...observability import trace_llm_call
from ...llm import get_openai_client

logger = get_logger()


@trace_llm_call(name="generate_answer_with_docs", tags=["node", "llm", "answer", "docs_only"])
def generate_answer_with_docs_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서만으로 답변 생성 (웹 검색 없음)
    
    캐시된 정책 문서를 기반으로 답변 생성
    GPT-4가 전체 문서에서 관련 정보를 찾아 답변
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (answer, evidence 추가)
    """
    try:
        current_query = state.get("current_query", "")
        policy_info = state.get("policy_info", {})
        retrieved_docs = state.get("retrieved_docs", [])
        messages = state.get("messages", [])
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "policy_qa_docs_only_prompt.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        
        # Render prompt
        prompt = template.render(
            policy_name=policy_info.get("name", ""),
            policy_overview=policy_info.get("overview", ""),
            apply_target=policy_info.get("apply_target", ""),
            support_description=policy_info.get("support_description", ""),
            retrieved_docs=retrieved_docs,
            user_question=current_query,
            chat_history=messages[-10:] if len(messages) > 10 else messages  # 최근 10개만
        )
        
        # Generate answer
        llm_client = get_openai_client()
        answer = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정부 정책 전문 상담사입니다. 제공된 정책 문서를 기반으로 정확하게 답변하세요."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Build evidence (DB 문서만)
        evidence = []
        for doc in retrieved_docs[:5]:  # 상위 5개만 evidence로 표시
            evidence.append({
                "type": "internal",
                "source": f"정책 문서 (섹션: {doc.get('doc_type', 'unknown')})",
                "content": doc.get("content", "")[:200] + "...",
                "policy_id": doc.get("policy_id"),
                "doc_id": doc.get("chunk_index"),
                "url": f"/policy/{doc.get('policy_id')}",
                "link_type": "policy_detail"
            })
        
        logger.info(
            "Answer generated from docs only",
            extra={
                "answer_length": len(answer),
                "evidence_count": len(evidence)
            }
        )
        
        return {
            **state,
            "answer": answer,
            "evidence": evidence
        }
        
    except Exception as e:
        logger.error(
            "Error in generate_answer_with_docs_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
            "evidence": [],
            "error": str(e)
        }


@trace_llm_call(name="generate_answer_web_only", tags=["node", "llm", "answer", "web_only"])
def generate_answer_web_only_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    웹 검색 결과만으로 답변 생성 (링크 중심)
    
    "링크 알려줘", "홈페이지" 등의 질문에 대해 웹 검색 결과로 답변
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (answer, evidence 추가)
    """
    try:
        current_query = state.get("current_query", "")
        policy_info = state.get("policy_info", {})
        web_sources = state.get("web_sources", [])
        messages = state.get("messages", [])
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "policy_qa_web_only_prompt.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        
        # Render prompt
        prompt = template.render(
            policy_name=policy_info.get("name", ""),
            web_sources=web_sources,
            user_question=current_query,
            chat_history=messages[-10:] if len(messages) > 10 else messages
        )
        
        # Generate answer
        llm_client = get_openai_client()
        answer = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정부 정책 전문 상담사입니다. 웹 검색 결과를 바탕으로 링크와 정보를 제공하세요."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Build evidence (웹 소스만)
        evidence = []
        for source in web_sources:
            evidence.append({
                "type": "web",
                "source": source.get("title", ""),
                "content": source.get("snippet", "")[:200] + "...",
                "url": source.get("url", ""),
                "fetched_date": source.get("fetched_date", ""),
                "link_type": "external"
            })
        
        logger.info(
            "Answer generated from web only",
            extra={
                "answer_length": len(answer),
                "evidence_count": len(evidence)
            }
        )
        
        return {
            **state,
            "answer": answer,
            "evidence": evidence
        }
        
    except Exception as e:
        logger.error(
            "Error in generate_answer_web_only_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
            "evidence": [],
            "error": str(e)
        }


@trace_llm_call(name="generate_answer_hybrid", tags=["node", "llm", "answer", "hybrid"])
def generate_answer_hybrid_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 + 웹 검색 결합 답변 생성
    
    정책 문서로 충분하지 않을 때 웹 검색 결과를 보완하여 답변
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (answer, evidence 추가)
    """
    try:
        current_query = state.get("current_query", "")
        policy_info = state.get("policy_info", {})
        retrieved_docs = state.get("retrieved_docs", [])
        web_sources = state.get("web_sources", [])
        messages = state.get("messages", [])
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "policy_qa_hybrid_prompt.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        
        # Render prompt
        prompt = template.render(
            policy_name=policy_info.get("name", ""),
            policy_overview=policy_info.get("overview", ""),
            apply_target=policy_info.get("apply_target", ""),
            support_description=policy_info.get("support_description", ""),
            retrieved_docs=retrieved_docs,
            web_sources=web_sources,
            user_question=current_query,
            chat_history=messages[-10:] if len(messages) > 10 else messages
        )
        
        # Generate answer
        llm_client = get_openai_client()
        answer = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정부 정책 전문 상담사입니다. 정책 문서와 웹 검색 결과를 모두 활용하여 답변하세요."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Build evidence (문서 + 웹)
        evidence = []
        
        # 1. DB 문서
        for doc in retrieved_docs[:5]:
            evidence.append({
                "type": "internal",
                "source": f"정책 문서 (섹션: {doc.get('doc_type', 'unknown')})",
                "content": doc.get("content", "")[:200] + "...",
                "policy_id": doc.get("policy_id"),
                "url": f"/policy/{doc.get('policy_id')}",
                "link_type": "policy_detail"
            })
        
        # 2. 웹 검색
        for source in web_sources:
            evidence.append({
                "type": "web",
                "source": source.get("title", ""),
                "content": source.get("snippet", "")[:200] + "...",
                "url": source.get("url", ""),
                "fetched_date": source.get("fetched_date", ""),
                "link_type": "external"
            })
        
        logger.info(
            "Answer generated from hybrid sources",
            extra={
                "answer_length": len(answer),
                "evidence_count": len(evidence),
                "docs_count": len(retrieved_docs),
                "web_count": len(web_sources)
            }
        )
        
        return {
            **state,
            "answer": answer,
            "evidence": evidence
        }
        
    except Exception as e:
        logger.error(
            "Error in generate_answer_hybrid_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
            "evidence": [],
            "error": str(e)
        }


# 하위 호환성을 위해 기존 함수명도 유지
generate_answer_node = generate_answer_with_docs_node
