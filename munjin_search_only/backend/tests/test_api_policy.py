"""
Policy API Tests
정책 검색 및 조회 API 테스트
"""

import pytest
from fastapi.testclient import TestClient

from src.app.db.models import Policy


def test_health_check(client: TestClient):
    """헬스체크 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_policies_empty(client: TestClient):
    """정책 목록 조회 (빈 결과)"""
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0


def test_get_policies_with_data(client: TestClient, test_db, sample_policy_data):
    """정책 목록 조회 (데이터 있음)"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    
    # Test API
    response = client.get("/api/v1/policies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["program_name"] == sample_policy_data["program_name"]


def test_get_policy_by_id(client: TestClient, test_db, sample_policy_data):
    """정책 상세 조회"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    test_db.refresh(policy)
    
    # Test API
    response = client.get(f"/api/v1/policy/{policy.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["program_name"] == sample_policy_data["program_name"]
    assert data["region"] == sample_policy_data["region"]


def test_get_policy_not_found(client: TestClient):
    """존재하지 않는 정책 조회"""
    response = client.get("/api/v1/policy/99999")
    assert response.status_code == 404


def test_search_policies_by_region(client: TestClient, test_db, sample_policy_data):
    """지역별 정책 검색"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    
    # Test API
    response = client.get("/api/v1/policies?region=서울")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_search_policies_by_category(client: TestClient, test_db, sample_policy_data):
    """카테고리별 정책 검색"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    
    # Test API
    response = client.get("/api/v1/policies?category=창업")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_get_regions(client: TestClient, test_db, sample_policy_data):
    """지역 목록 조회"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    
    # Test API
    response = client.get("/api/v1/policies/regions")
    assert response.status_code == 200
    data = response.json()
    assert "서울" in data


def test_get_categories(client: TestClient, test_db, sample_policy_data):
    """카테고리 목록 조회"""
    # Insert test policy
    policy = Policy(**sample_policy_data)
    test_db.add(policy)
    test_db.commit()
    
    # Test API
    response = client.get("/api/v1/policies/categories")
    assert response.status_code == 200
    data = response.json()
    assert "창업" in data

