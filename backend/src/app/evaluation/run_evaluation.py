"""
QA Agent 평가 실행
"""

from langsmith import Client
from langsmith.evaluation import evaluate
from ..agent.controller import AgentController
from ..config.logger import get_logger
from .evaluators import (
    check_answer_relevance,
    check_citation_format,
    check_query_classification,
    check_evidence_type,
    check_response_time
)

logger = get_logger()


def qa_agent_target_function(inputs: dict) -> dict:
    """
    평가 대상 함수
    
    LangSmith가 호출할 함수로, QA Agent의 실제 실행 결과를 반환
    
    Args:
        inputs: {session_id, policy_id, current_query}
    
    Returns:
        dict: {answer, evidence, query_type, need_web_search}
    """
    try:
        controller = AgentController()
        
        result = controller.run_qa(
            session_id=inputs["session_id"],
            policy_id=inputs["policy_id"],
            current_query=inputs["current_query"]
        )
        
        return {
            "answer": result.get("answer", ""),
            "evidence": result.get("evidence", []),
            "query_type": result.get("query_type", ""),
            "need_web_search": result.get("need_web_search", False),
        }
    except Exception as e:
        logger.error(f"평가 실행 중 에러: {e}", exc_info=True)
        return {
            "answer": f"ERROR: {str(e)}",
            "evidence": [],
            "query_type": "ERROR",
            "need_web_search": False,
        }


def run_evaluation(dataset_name: str = "qaagent-policy-qa-eval-v1"):
    """
    QA Agent 평가 실행
    
    Args:
        dataset_name: LangSmith 데이터셋 이름
    
    Returns:
        평가 결과
    """
    try:
        logger.info(f"평가 시작: 데이터셋 '{dataset_name}'")
        
        # 평가 실행
        results = evaluate(
            qa_agent_target_function,
            data=dataset_name,
            evaluators=[
                check_answer_relevance,
                check_citation_format,
                check_query_classification,
                check_evidence_type,
                check_response_time,
            ],
            experiment_prefix="qaagent-eval",
            metadata={
                "version": "v2_cache",
                "model": "gpt-4o-mini",
                "description": "QA Agent 자동 평가 (캐시 시스템 적용)"
            },
        )
        
        logger.info("\n✅ 평가 완료!")
        logger.info(f"   - 결과: {results}")
        logger.info(f"   - LangSmith에서 상세 결과 확인 가능")
        logger.info(f"   - URL: https://smith.langchain.com")
        
        return results
        
    except Exception as e:
        logger.error(f"평가 실행 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_evaluation()

