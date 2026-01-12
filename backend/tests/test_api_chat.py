"""
Chat API Tests
Q&A 채팅 API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.app.db.models import Policy


@pytest.mark.skip(reason="Requires OpenAI API key and Qdrant")
def test_chat_endpoint(client: TestClient, test_db, sample_policy_data, sample_chat_request):
    """채팅 엔드포인트 테스트 (통합 테스트)"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    
    # Test API
    response = client.post("/api/v1/chat", json=sample_chat_request)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "answer" in data
    assert "evidence" in data


def test_chat_endpoint_mock(client: TestClient, sample_chat_request):
    """채팅 엔드포인트 테스트 (Mock)"""
    with patch("src.app.agent.controller.AgentController.run_qa_workflow") as mock_run:
        # Mock response
        mock_run.return_value = {
            "session_id": "test-session-001",
            "answer": "테스트 답변입니다.",
            "evidence": [],
            "web_sources": []
        }
        
        # Test API
        response = client.post("/api/v1/chat", json=sample_chat_request)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-001"
        assert "answer" in data


def test_session_reset(client: TestClient):
    """세션 리셋 테스트"""
    response = client.post("/api/v1/session/reset", json={"session_id": "test-session-001"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "세션이 초기화되었습니다."

