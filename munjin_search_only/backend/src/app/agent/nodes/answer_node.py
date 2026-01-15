"""
Answer Generation Node
LLM으로 최종 답변 생성
"""

from typing import Dict, Any
from jinja2 import Template
from pathlib import Path

from ...config.logger import get_logger
from ...observability import trace_llm_call
from ...llm import get_openai_client
from ...db.engine import get_db
from ...db.models import Policy

logger = get_logger()


@trace_llm_call(name="generate_answer", tags=["node", "llm", "answer"])
def generate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM으로 답변 생성
    
    정책 정보 + 검색된 문서 + 웹 소스를 기반으로 답변 생성
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (answer, evidence 추가)
    """
    try:
        current_query = state.get("current_query", "")
        policy_id = state.get("policy_id")
        retrieved_docs = state.get("retrieved_docs", [])
        web_sources = state.get("web_sources", [])
        
        # Get policy information
        policy_info = {}
        if policy_id:
            with get_db() as db:
                policy = db.query(Policy).filter(Policy.id == policy_id).first()
                if policy:
                    policy_info = {
                        "policy_name": policy.program_name,
                        "policy_overview": policy.program_overview or "",
                        "apply_target": policy.apply_target or "",
                        "support_description": policy.support_description or ""
                    }
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "policy_qa_prompt.jinja2"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        template = Template(template_str)
        
        # Render prompt
        prompt = template.render(
            policy_name=policy_info.get("policy_name", ""),
            policy_overview=policy_info.get("policy_overview", ""),
            apply_target=policy_info.get("apply_target", ""),
            support_description=policy_info.get("support_description", ""),
            retrieved_docs=retrieved_docs,
            web_sources=web_sources,
            user_question=current_query
        )
        
        # Generate answer
        llm_client = get_openai_client()
        answer = llm_client.generate(
            messages=[
                {"role": "system", "content": "당신은 정부 정책 전문 상담사입니다."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Build evidence
        evidence = []
        
        # Add internal docs as evidence
        for i, doc in enumerate(retrieved_docs, 1):
            evidence.append({
                "type": "internal",
                "source": f"정책 문서 (섹션: {doc.get('doc_type', 'unknown')})",
                "content": doc.get("content", "")[:200] + "...",
                "score": doc.get("score", 0.0)
            })
        
        # Add web sources as evidence
        for i, source in enumerate(web_sources, 1):
            evidence.append({
                "type": "web",
                "source": source.get("title", ""),
                "content": source.get("snippet", "")[:200] + "...",
                "url": source.get("url", ""),
                "fetched_date": source.get("fetched_date", "")
            })
        
        logger.info(
            "Answer generated",
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
            "Error in generate_answer_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
            "evidence": [],
            "error": str(e)
        }

