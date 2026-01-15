"""
Search Check Sufficiency Node
검색 결과의 충분성을 3단계로 판단하여 웹 검색 필요 여부 결정

3단계 충분성 검증:
1. Top-K 점수 검사 (0.65 기준)
2. Cosine 유사도 재검증
3. LLM Grader (필요시)
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from jinja2 import Template

from ....config.logger import get_logger
from ....observability import trace_workflow, trace_llm_call, get_feature_tags
from ....llm import get_openai_client

logger = get_logger()

# 충분성 판단 기준 상수
SCORE_THRESHOLD_TOP1 = 0.65          # top_1 유사도 기준 (1단계)
SCORE_THRESHOLD_COSINE = 0.60        # cosine 유사도 재검증 기준 (2단계)
MIN_RESULTS_COUNT = 2                 # 최소 결과 수
SCORE_THRESHOLD_AVG = 0.55           # 평균 유사도 기준 (보조)
MIN_HIGH_SCORE_RESULTS = 1           # 높은 점수 결과 최소 개수
HIGH_SCORE_THRESHOLD = 0.70          # 높은 점수 기준
LLM_GRADER_THRESHOLD = 0.70          # LLM Grader 관련성 기준


@trace_llm_call(
    name="llm_grader",
    tags=["node", "search", "llm", "grader"]
)
def _llm_grade_relevance(
    query: str,
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    """
    LLM을 사용하여 검색 결과의 관련성을 평가 (3단계)

    Args:
        query: 원본 검색 쿼리
        policy: 평가할 정책 정보

    Returns:
        Dict: {is_relevant: bool, relevance_score: float, reason: str}
    """
    try:
        # Load Jinja2 template
        prompt_path = Path(__file__).parent.parent.parent.parent / "prompts" / "search_grader.jinja2"

        with open(prompt_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())

        # Render prompt
        prompt = template.render(
            query=query,
            policy=policy
        )

        # Call LLM
        llm_client = get_openai_client()
        response = llm_client.generate_with_system(
            system_prompt="당신은 검색 결과 관련성 평가 전문가입니다. 반드시 유효한 JSON만 응답하세요.",
            user_message=prompt,
            temperature=0.0
        )

        # Parse JSON response
        clean_response = response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.startswith("```"):
            clean_response = clean_response[3:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        clean_response = clean_response.strip()

        result = json.loads(clean_response)

        return {
            "is_relevant": result.get("is_relevant", False),
            "relevance_score": result.get("relevance_score", 0.0),
            "reason": result.get("reason", "")
        }

    except Exception as e:
        logger.warning(
            "LLM grader failed, using fallback",
            extra={"error": str(e)}
        )
        # Fallback: 점수 기반 판단
        score = policy.get("score", 0.0)
        return {
            "is_relevant": score >= 0.65,
            "relevance_score": score,
            "reason": f"LLM 평가 실패, 점수 기반 판단: {score:.2f}"
        }


def _check_cosine_similarity(
    retrieved_docs: List[Dict[str, Any]],
    threshold: float = SCORE_THRESHOLD_COSINE
) -> Dict[str, Any]:
    """
    Cosine 유사도 재검증 (2단계)

    Args:
        retrieved_docs: 검색된 문서 리스트
        threshold: 유사도 기준

    Returns:
        Dict: {passed: bool, avg_score: float, high_score_count: int, details: str}
    """
    if not retrieved_docs:
        return {
            "passed": False,
            "avg_score": 0.0,
            "high_score_count": 0,
            "details": "검색 결과 없음"
        }

    scores = [doc.get("score", 0.0) for doc in retrieved_docs]
    avg_score = sum(scores) / len(scores)
    high_score_count = sum(1 for s in scores if s >= HIGH_SCORE_THRESHOLD)

    # 통과 조건: 평균 점수 >= threshold 또는 고점수 결과 >= 1개
    passed = avg_score >= threshold or high_score_count >= MIN_HIGH_SCORE_RESULTS

    details = f"평균 유사도: {avg_score:.2f}, 고점수({HIGH_SCORE_THRESHOLD}+) 결과: {high_score_count}건"

    return {
        "passed": passed,
        "avg_score": avg_score,
        "high_score_count": high_score_count,
        "details": details
    }


@trace_workflow(
    name="search_check_sufficiency",
    tags=["node", "search", "check", "3-stage"]
)
def search_check_sufficiency_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색 결과의 충분성을 3단계로 판단

    3단계 충분성 검증:
    1. [1단계] Top-K 점수 검사: top_1 >= 0.65
    2. [2단계] Cosine 유사도 재검증: 평균 >= 0.60 또는 고점수 결과 존재
    3. [3단계] LLM Grader: 1,2단계 통과했지만 확신이 없을 때 LLM으로 관련성 평가

    Args:
        state: 현재 상태 (retrieved_docs, top_score, parsed_query 필수)

    Returns:
        Dict: 업데이트된 상태 (is_sufficient, sufficiency_reason, grader_result 추가)
    """
    try:
        retrieved_docs = state.get("retrieved_docs", [])
        top_score = state.get("top_score", 0.0)
        parsed_query = state.get("parsed_query", {})
        original_query = state.get("original_query", "")

        stage_results = []
        grader_result = None

        # =====================================================================
        # 결과가 없는 경우: 즉시 불충분 판정
        # =====================================================================
        if not retrieved_docs:
            return {
                **state,
                "is_sufficient": False,
                "sufficiency_reason": "[0단계] 검색 결과가 없습니다. 웹 검색을 수행합니다.",
                "grader_result": None
            }

        # =====================================================================
        # 1단계: Top-K 점수 검사
        # =====================================================================
        stage1_passed = top_score >= SCORE_THRESHOLD_TOP1
        stage_results.append(
            f"[1단계 Top-K] top_1={top_score:.2f} (기준: {SCORE_THRESHOLD_TOP1}) → {'통과' if stage1_passed else '실패'}"
        )

        if not stage1_passed:
            # 1단계 실패: 웹 검색 필요
            return {
                **state,
                "is_sufficient": False,
                "sufficiency_reason": f"[1단계 실패] 최고 유사도({top_score:.2f})가 기준({SCORE_THRESHOLD_TOP1})보다 낮습니다. 웹 검색으로 보충합니다.\n" + "\n".join(stage_results),
                "grader_result": None
            }

        # =====================================================================
        # 2단계: Cosine 유사도 재검증
        # =====================================================================
        cosine_result = _check_cosine_similarity(retrieved_docs)
        stage2_passed = cosine_result["passed"]
        stage_results.append(
            f"[2단계 Cosine] {cosine_result['details']} → {'통과' if stage2_passed else '실패'}"
        )

        if not stage2_passed:
            # 2단계 실패: 웹 검색 필요
            return {
                **state,
                "is_sufficient": False,
                "sufficiency_reason": f"[2단계 실패] Cosine 유사도 재검증 실패. {cosine_result['details']}. 웹 검색으로 보충합니다.\n" + "\n".join(stage_results),
                "grader_result": None
            }

        # =====================================================================
        # 1,2단계 통과: 추가 확인 필요 여부 판단
        # =====================================================================
        # 최소 결과 수 검사
        if len(retrieved_docs) < MIN_RESULTS_COUNT:
            return {
                **state,
                "is_sufficient": False,
                "sufficiency_reason": f"[결과 수 부족] 검색 결과({len(retrieved_docs)}건)가 최소 기준({MIN_RESULTS_COUNT}건)보다 적습니다.\n" + "\n".join(stage_results),
                "grader_result": None
            }

        # 고신뢰도 판단: top_score >= 0.75 이면 LLM Grader 스킵
        if top_score >= 0.75 and cosine_result["high_score_count"] >= 1:
            stage_results.append(
                f"[고신뢰도] top_score={top_score:.2f} >= 0.75, 고점수 결과 있음 → LLM Grader 스킵"
            )
            logger.info(
                "Sufficiency check completed (high confidence)",
                extra={
                    "is_sufficient": True,
                    "top_score": top_score,
                    "results_count": len(retrieved_docs),
                    "stage": "high_confidence"
                }
            )
            return {
                **state,
                "is_sufficient": True,
                "sufficiency_reason": f"[충분] 고신뢰도 검색 결과.\n" + "\n".join(stage_results),
                "grader_result": None
            }

        # =====================================================================
        # 3단계: LLM Grader (중간 신뢰도 구간)
        # =====================================================================
        # 0.65 <= top_score < 0.75 구간에서 LLM으로 관련성 최종 확인
        stage_results.append(
            f"[3단계 LLM Grader] 중간 신뢰도 구간({top_score:.2f}), LLM 관련성 평가 수행"
        )

        # 상위 1개 결과에 대해 LLM Grader 수행
        top_doc = retrieved_docs[0]
        grader_result = _llm_grade_relevance(original_query, top_doc)

        stage_results.append(
            f"[3단계 결과] is_relevant={grader_result['is_relevant']}, score={grader_result['relevance_score']:.2f}, reason={grader_result['reason']}"
        )

        logger.info(
            "Sufficiency check completed (with LLM grader)",
            extra={
                "is_sufficient": grader_result["is_relevant"],
                "top_score": top_score,
                "results_count": len(retrieved_docs),
                "grader_score": grader_result["relevance_score"],
                "stage": "llm_grader"
            }
        )

        if grader_result["is_relevant"] and grader_result["relevance_score"] >= LLM_GRADER_THRESHOLD:
            # LLM Grader 통과
            return {
                **state,
                "is_sufficient": True,
                "sufficiency_reason": f"[충분] 3단계 검증 모두 통과.\n" + "\n".join(stage_results),
                "grader_result": grader_result
            }
        else:
            # LLM Grader 실패
            return {
                **state,
                "is_sufficient": False,
                "sufficiency_reason": f"[3단계 실패] LLM Grader 관련성 부족. {grader_result['reason']}. 웹 검색으로 보충합니다.\n" + "\n".join(stage_results),
                "grader_result": grader_result
            }

    except Exception as e:
        logger.error(
            "Error in search_check_sufficiency_node",
            extra={"error": str(e)},
            exc_info=True
        )
        # 에러 시 웹 검색 수행
        return {
            **state,
            "is_sufficient": False,
            "sufficiency_reason": f"충분성 검사 중 오류 발생: {str(e)}. 웹 검색으로 보충합니다.",
            "grader_result": None,
            "error": str(e)
        }
