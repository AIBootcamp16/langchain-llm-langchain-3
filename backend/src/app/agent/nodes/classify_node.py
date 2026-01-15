"""
Classify Query Node
사용자 질문 유형 분류 (WEB_ONLY vs POLICY_QA)
"""

from typing import Dict, Any
from ...config.logger import get_logger
from ...observability import trace_workflow
from ...llm.openai_client import OpenAIClient

logger = get_logger()
llm_client = OpenAIClient()


@trace_workflow(name="classify_query_type", tags=["node", "classify"])
def classify_query_type_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    사용자 질문 유형 분류: WEB_ONLY vs POLICY_QA
    
    1차 키워드 기반:
    - "링크", "홈페이지" 등 → WEB_ONLY
    
    2차 LLM 기반:
    - 정책 내용과 관련 있음 → POLICY_QA
    - 정책과 무관한 일반 질문 → WEB_ONLY (웹 검색 필요)
    
    Args:
        state: 현재 상태
    
    Returns:
        Dict: 업데이트된 상태 (query_type 포함)
    """
    try:
        current_query = state.get("current_query", "")
        
        query_lower = current_query.lower()
        
        # 1차: WEB_ONLY 키워드 (링크/홈페이지 요청)
        web_only_keywords = [
            "링크", "url", "홈페이지", "사이트", "웹사이트",
            "어디서 신청", "신청 방법", "신청하는 방법",
            "신청서 다운로드", "양식 다운로드", 
            "접수", "접수처", "공고문"
        ]
        
        if any(keyword in query_lower for keyword in web_only_keywords):
            query_type = "WEB_ONLY"
            logger.info(
                "Query classified as WEB_ONLY (keyword match)",
                extra={
                    "query": current_query,
                    "query_type": query_type
                }
            )
            return {
                **state,
                "query_type": query_type,
                "need_web_search": False
            }
        
        # 2차: POLICY_QA 키워드 (정책 내용 질문) - 빠른 경로! ⚡
        policy_qa_keywords = [
            "지원금", "지원 금액", "지원", "금액", "얼마",
            "대상", "자격", "조건", "요건",
            "신청 기간", "기간", "언제", "마감",
            "방법", "어떻게", "절차",
            "혜택", "내용", "뭐", "무엇", "설명"
        ]
        
        if any(keyword in query_lower for keyword in policy_qa_keywords):
            query_type = "POLICY_QA"
            logger.info(
                "Query classified as POLICY_QA (keyword match - fast path)",
                extra={
                    "query": current_query,
                    "query_type": query_type
                }
            )
            return {
                **state,
                "query_type": query_type,
                "need_web_search": False
            }
        
        # 2.5차: 정책 컨텍스트가 있으면 (정책 Q&A 페이지) 기본값은 POLICY_QA
        # 사용자가 이미 특정 정책에 대해 묻고 있다는 것이 명확함
        policy_info = state.get("policy_info", {})
        if policy_info:
            # 정책 페이지에서의 질문은 기본적으로 POLICY_QA
            # 단, WEB_ONLY 키워드가 없었다면 → POLICY_QA
            query_type = "POLICY_QA"
            logger.info(
                "Query classified as POLICY_QA (policy context - default)",
                extra={
                    "query": current_query,
                    "query_type": query_type,
                    "policy_name": policy_info.get("name", "")
                }
            )
            return {
                **state,
                "query_type": query_type,
                "need_web_search": False
            }
        
        # 3차: LLM 기반 지능적 분류 (애매한 경우만)
        # 정책 컨텍스트 추가 (사용자가 이미 정책 페이지에 있음)
        policy_info = state.get("policy_info", {})
        policy_name = policy_info.get("name", "특정 정책")
        
        context_info = f"\n\n🎯 중요: 사용자는 현재 '{policy_name}' 정책 페이지에서 질문하고 있습니다.\n정책명이나 정책과 관련된 용어가 포함되어 있다면 POLICY_QA입니다."
        
        classification_prompt = f"""다음 질문이 "정책/지원금/사업" 내용과 관련이 있는지 판단해주세요.{context_info}

질문: {current_query}

판단 기준:
- 정책/지원금/사업의 지원 내용, 대상, 금액, 조건, 신청 기간 등을 묻는 질문 → "POLICY_QA"
- 정책명이나 정책 관련 용어를 묻는 질문 → "POLICY_QA"
- 정책과 완전히 무관한 일반 지식, 장소, 인물, 개념 등을 묻는 질문 → "WEB_ONLY"
- 애매한 경우 정책과 약간이라도 관련 있으면 → "POLICY_QA"

예시:
- "지원 금액은?" → POLICY_QA
- "신청 대상은?" → POLICY_QA
- "창조기업" → POLICY_QA (정책명)
- "1인 창업" → POLICY_QA (정책 관련 용어)
- "전주한옥마을은 어디야?" → WEB_ONLY (정책 무관)
- "AI는 뭐야?" → WEB_ONLY (정책 무관, 단 정책이 AI 관련이면 POLICY_QA)

답변 형식 (반드시 이 중 하나만):
POLICY_QA
WEB_ONLY"""

        try:
            llm_response = llm_client.generate(
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.0,
                max_tokens=10
            )
            
            query_type = llm_response.strip().upper()
            
            # Validation
            if query_type not in ["POLICY_QA", "WEB_ONLY"]:
                logger.warning(f"Invalid LLM classification: {query_type}, defaulting to POLICY_QA")
                query_type = "POLICY_QA"
                
        except Exception as llm_error:
            logger.warning(
                "LLM classification failed, defaulting to POLICY_QA",
                extra={"error": str(llm_error)}
            )
            query_type = "POLICY_QA"
        
        logger.info(
            "Query type classified",
            extra={
                "query": current_query,
                "query_type": query_type
            }
        )
        
        return {
            **state,
            "query_type": query_type,
            "need_web_search": False  # 기본값 (추후 check_sufficiency에서 결정)
        }
        
    except Exception as e:
        logger.error(
            "Error in classify_query_type_node",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            **state,
            "query_type": "POLICY_QA",  # 에러 시 기본값
            "need_web_search": False,
            "error": str(e)
        }


# 하위 호환성을 위해 기존 함수명도 유지
classify_query_node = classify_query_type_node

