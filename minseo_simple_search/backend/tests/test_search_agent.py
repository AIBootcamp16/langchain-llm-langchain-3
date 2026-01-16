"""
Search Agent Tests
정책 검색 에이전트 워크플로우 단위 테스트
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.app.agent.controller import AgentController
from src.app.db.models import Policy

# Mock Data Setup
MOCK_POLICY_ORM = Policy(
    id=1,
    program_name="청년 창업 지원",
    region="서울",
    category="사업화",
    program_overview="서울시 청년 창업 지원 사업입니다.",
    created_at=datetime.now()
)
# 검색 로직에서 동적으로 할당되는 score 속성
MOCK_POLICY_ORM.score = 0.0

@pytest.fixture
def mock_db_session():
    """SQLAlchemy Session Mock"""
    session = MagicMock()
    # query().filter().order_by().all() 체이닝 Mock
    query_mock = session.query.return_value
    filter_mock = query_mock.filter.return_value
    order_by_mock = filter_mock.order_by.return_value
    
    # 기본적으로 MOCK_POLICY_ORM 반환
    filter_mock.all.return_value = [MOCK_POLICY_ORM]
    order_by_mock.all.return_value = [MOCK_POLICY_ORM]
    
    return session

@patch("src.app.agent.nodes.grade_node.OpenAIClient")
@patch("src.app.agent.nodes.query_understanding_node.OpenAIClient")
@patch("src.app.agent.nodes.retrieve_node.get_qdrant_manager")
@patch("src.app.agent.nodes.retrieve_node.get_embedder")
def test_search_agent_sufficient_results(mock_embedder, mock_qdrant, mock_openai_query, mock_openai_grade, mock_db_session):
    """
    테스트 시나리오 1: 검색 결과가 충분한 경우 (웹 검색 수행 X)
    - Qdrant 점수가 0.65 이상인 정책이 존재함 -> 웹 검색 없이 종료
    """
    # 1. LLM Mock (Query Understanding)
    mock_llm = mock_openai_query.return_value
    mock_llm.generate.return_value = '{"keywords": "청년 창업", "category": "사업화", "region": "서울", "sort_by": "relevance"}'
    
    # 2. Embedder Mock
    mock_embedder.return_value.embed_text.return_value = [0.1] * 1024
    
    # 3. Qdrant Mock (High Score)
    mock_qdrant.return_value.search.return_value = [
        {"payload": {"policy_id": 1}, "score": 0.85}  # Threshold 0.65 이상
    ]
    
    # 4. Run Search
    result = AgentController.run_search("서울 청년 창업 지원해줘", mock_db_session)
    
    # 5. Assertions
    assert result["total"] == 1
    assert result["policies"][0].program_name == "청년 창업 지원"
    # 웹 검색 결과(음수 ID)가 없어야 함
    assert all(p.id > 0 for p in result["policies"])

@patch("src.app.agent.nodes.grade_node.OpenAIClient")
@patch("src.app.agent.nodes.query_understanding_node.OpenAIClient")
@patch("src.app.agent.nodes.retrieve_node.get_qdrant_manager")
@patch("src.app.agent.nodes.retrieve_node.get_embedder")
@patch("src.app.agent.nodes.web_search_node.get_tavily_client")
def test_search_agent_insufficient_results(mock_tavily, mock_embedder, mock_qdrant, mock_openai_query, mock_openai_grade, mock_db_session):
    """
    테스트 시나리오 2: 검색 결과가 불충분한 경우 (웹 검색 수행 O)
    - Qdrant 점수가 0.65 미만 -> LLM Grader가 '관련 없음(no)' 판정 -> 웹 검색 실행
    """
    # 1. LLM Mock (Query Understanding)
    mock_llm_query = mock_openai_query.return_value
    mock_llm_query.generate.return_value = '{"keywords": "우주 여행", "category": null, "region": null, "sort_by": "relevance"}'
    
    # 2. LLM Mock (Grader) - 관련 없음 판정
    mock_llm_grade = mock_openai_grade.return_value
    # Grader가 "no"를 반환해야 웹 검색으로 넘어감
    mock_llm_grade.generate.return_value = '{"score": "no", "reason": "주제 불일치"}'
    
    # 2. Embedder Mock
    mock_embedder.return_value.embed_text.return_value = [0.1] * 1024
    
    # 3. Qdrant Mock (Low Score)
    mock_qdrant.return_value.search.return_value = [
        {"payload": {"policy_id": 1}, "score": 0.4}  # Threshold 0.65 미만
    ]
    
    # 4. Tavily Mock (Web Search)
    mock_tavily.return_value.search.return_value = [
        {"title": "정부 우주 산업 지원 공고", "content": "내용...", "url": "http://example.com", "score": 0.9}
    ]
    
    # 5. Run Search
    result = AgentController.run_search("우주 여행 지원", mock_db_session)
    
    # 6. Assertions
    # DB 결과(1개) + 웹 검색 결과(1개) = 총 2개
    assert len(result["policies"]) == 2
    
    # 웹 검색 결과 확인 (음수 ID로 변환됨)
    web_policy = result["policies"][1]
    assert web_policy.region == "웹 검색"
    assert web_policy.program_name == "정부 우주 산업 지원 공고"
    
    # Tavily 클라이언트가 호출되었는지 확인
    mock_tavily.return_value.search.assert_called_once()

@patch("src.app.agent.nodes.grade_node.OpenAIClient")
@patch("src.app.agent.nodes.query_understanding_node.OpenAIClient")
@patch("src.app.agent.nodes.retrieve_node.get_qdrant_manager")
@patch("src.app.agent.nodes.retrieve_node.get_embedder")
@patch("src.app.agent.nodes.web_search_node.get_tavily_client")
def test_search_agent_low_score_but_relevant(mock_tavily, mock_embedder, mock_qdrant, mock_openai_query, mock_openai_grade, mock_db_session):
    """
    테스트 시나리오 3: 점수는 낮지만 LLM이 관련 있다고 판단한 경우 (웹 검색 수행 X)
    - Qdrant 점수 0.65 미만 -> LLM Grader가 '관련 있음(yes)' 판정 -> 웹 검색 없이 종료
    """
    # 1. LLM Mock (Query Understanding)
    mock_llm_query = mock_openai_query.return_value
    mock_llm_query.generate.return_value = '{"keywords": "청년 창업", "category": "사업화", "region": "서울", "sort_by": "relevance"}'
    
    # 2. LLM Mock (Grader) - 관련 있음 판정
    mock_llm_grade = mock_openai_grade.return_value
    mock_llm_grade.generate.return_value = '{"score": "yes", "reason": "내용 일치"}'
    
    # 3. Embedder Mock
    mock_embedder.return_value.embed_text.return_value = [0.1] * 1024
    
    # 4. Qdrant Mock (Low Score)
    mock_qdrant.return_value.search.return_value = [
        {"payload": {"policy_id": 1}, "score": 0.5}  # Threshold 0.65 미만
    ]
    
    # 5. Run Search
    result = AgentController.run_search("서울 청년 창업", mock_db_session)
    
    # 6. Assertions
    # 웹 검색 없이 DB 결과만 반환되어야 함
    assert len(result["policies"]) == 1
    assert result["policies"][0].id == 1
    
    # Tavily 클라이언트가 호출되지 않아야 함
    mock_tavily.return_value.search.assert_not_called()