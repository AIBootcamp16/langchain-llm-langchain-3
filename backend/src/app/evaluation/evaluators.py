"""
QA Agent 평가 함수들
"""

from typing import Dict, Any


def check_answer_relevance(run, example) -> Dict[str, Any]:
    """
    답변의 관련성 평가
    
    - 질문에 대한 답변이 적절한가?
    - 기대하는 키워드가 포함되어 있는가?
    """
    answer = run.outputs.get("answer", "")
    expected_keywords = example.outputs.get("answer_should_contain", [])
    
    if not expected_keywords:
        return {"key": "answer_relevance", "score": None}
    
    # 키워드 포함 여부 확인
    found_keywords = [kw for kw in expected_keywords if kw in answer]
    score = len(found_keywords) / len(expected_keywords)
    
    return {
        "key": "answer_relevance",
        "score": score,
        "comment": f"Found {len(found_keywords)}/{len(expected_keywords)} keywords"
    }


def check_citation_format(run, example) -> Dict[str, Any]:
    """
    인용 형식 평가
    
    - [정책문서 X] 또는 [웹 X] 형식이 포함되어 있는가?
    """
    answer = run.outputs.get("answer", "")
    expected_format = example.outputs.get("citation_format", None)
    
    if not expected_format:
        return {"key": "citation_format", "score": None}
    
    # 정책문서 인용
    if "[정책문서" in expected_format:
        has_citation = "[정책문서" in answer
    # 웹 인용
    elif "[웹" in expected_format:
        has_citation = "[웹" in answer
    else:
        has_citation = False
    
    return {
        "key": "citation_format",
        "score": 1.0 if has_citation else 0.0,
        "comment": f"Citation format: {expected_format}"
    }


def check_query_classification(run, example) -> Dict[str, Any]:
    """
    질문 분류 평가
    
    - WEB_ONLY vs POLICY_QA 분류가 올바른가?
    """
    query_type = run.outputs.get("query_type", None)
    expected_type = example.outputs.get("query_type", None)
    
    if not expected_type:
        return {"key": "query_classification", "score": None}
    
    is_correct = (query_type == expected_type)
    
    return {
        "key": "query_classification",
        "score": 1.0 if is_correct else 0.0,
        "comment": f"Expected: {expected_type}, Got: {query_type}"
    }


def check_evidence_type(run, example) -> Dict[str, Any]:
    """
    근거 유형 평가
    
    - internal (정책 문서) vs web 근거가 올바르게 사용되었는가?
    """
    evidence = run.outputs.get("evidence", [])
    expected_type = example.outputs.get("evidence_type", None)
    
    if not expected_type:
        return {"key": "evidence_type", "score": None}
    
    if not evidence:
        return {
            "key": "evidence_type",
            "score": 0.0,
            "comment": "No evidence provided"
        }
    
    # Evidence 유형 확인
    evidence_types = [e.get("type") for e in evidence]
    has_expected = expected_type in evidence_types
    
    return {
        "key": "evidence_type",
        "score": 1.0 if has_expected else 0.0,
        "comment": f"Expected: {expected_type}, Got: {evidence_types}"
    }


def check_response_time(run, example) -> Dict[str, Any]:
    """
    응답 시간 평가
    
    - 3초 이내: 1.0
    - 3-5초: 0.5
    - 5초 이상: 0.0
    """
    # LangSmith run에서 실행 시간 가져오기
    latency = run.latency if hasattr(run, 'latency') else None
    
    if latency is None:
        return {"key": "response_time", "score": None}
    
    # 밀리초 → 초 변환
    latency_seconds = latency / 1000 if latency > 100 else latency
    
    if latency_seconds <= 3:
        score = 1.0
    elif latency_seconds <= 5:
        score = 0.5
    else:
        score = 0.0
    
    return {
        "key": "response_time",
        "score": score,
        "comment": f"Latency: {latency_seconds:.2f}s"
    }

