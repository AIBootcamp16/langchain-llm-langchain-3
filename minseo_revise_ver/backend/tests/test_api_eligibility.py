"""
Eligibility API Tests
자격 확인 API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.app.db.models import Policy


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_eligibility_start(client: TestClient, test_db, sample_policy_data):
    """자격 확인 시작 테스트 (통합 테스트)"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    test_db.refresh(policy)
    
    # Test API
    response = client.post("/api/v1/eligibility/start", json={"policy_id": policy.id})
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "question" in data
    assert "progress" in data


def test_eligibility_start_mock(client: TestClient, test_db, sample_policy_data):
    """자격 확인 시작 테스트 (Mock)"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    test_db.refresh(policy)
    
    with patch("src.app.agent.workflows.eligibility_workflow.run_eligibility_start") as mock_start:
        # Mock response
        mock_start.return_value = {
            "session_id": "test-eligibility-001",
            "policy_id": policy.id,
            "current_question": "귀하의 사업자 등록 상태를 알려주세요.",
            "conditions": [
                {"name": "사업자 등록", "status": "UNKNOWN"}
            ],
            "current_condition_index": 0
        }
        
        # Test API
        response = client.post("/api/v1/eligibility/start", json={"policy_id": policy.id})
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "question" in data


def test_eligibility_start_policy_not_found(client: TestClient):
    """존재하지 않는 정책으로 자격 확인 시작"""
    response = client.post("/api/v1/eligibility/start", json={"policy_id": 99999})
    assert response.status_code == 404


@pytest.mark.skip(reason="Requires session setup")
def test_eligibility_answer(client: TestClient):
    """자격 확인 답변 테스트"""
    # This test requires a valid session from eligibility_start
    pass


def test_eligibility_result_not_found(client: TestClient):
    """존재하지 않는 세션의 결과 조회"""
    response = client.get("/api/v1/eligibility/result/invalid-session")
    assert response.status_code == 404

