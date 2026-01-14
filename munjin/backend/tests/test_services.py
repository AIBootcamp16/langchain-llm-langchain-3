"""
Service Layer Tests
서비스 레이어 단위 테스트
"""

import pytest
from unittest.mock import MagicMock, patch

from src.app.services.policy_search_service import PolicySearchService
from src.app.services.web_source_service import WebSourceService
from src.app.db.models import Policy, WebSource


def test_policy_search_service_init(test_db):
    """PolicySearchService 초기화 테스트"""
    service = PolicySearchService(test_db)
    assert service.db == test_db


def test_web_source_service_save(test_db):
    """WebSourceService 저장 테스트"""
    service = WebSourceService(test_db)
    
    sources = [
        {
            "url": "https://example.com",
            "title": "Test Source",
            "snippet": "Test snippet",
            "source_type": "test"
        }
    ]
    
    saved = service.save_web_sources(
        session_id="test-session",
        policy_id=1,
        query="test query",
        sources=sources
    )
    
    assert len(saved) == 1
    assert saved[0].url == "https://example.com"


def test_web_source_service_get(test_db):
    """WebSourceService 조회 테스트"""
    service = WebSourceService(test_db)
    
    # Save first
    sources = [
        {
            "url": "https://example.com",
            "title": "Test Source",
            "snippet": "Test snippet",
            "source_type": "test"
        }
    ]
    
    service.save_web_sources(
        session_id="test-session",
        policy_id=1,
        query="test query",
        sources=sources
    )
    
    # Get
    retrieved = service.get_web_sources(session_id="test-session")
    assert len(retrieved) == 1
    assert retrieved[0].url == "https://example.com"


@pytest.mark.skip(reason="Requires Qdrant connection")
def test_policy_search_service_hybrid_search(test_db):
    """PolicySearchService 하이브리드 검색 테스트"""
    service = PolicySearchService(test_db)
    
    results = service.hybrid_search(
        query="창업 지원",
        region=None,
        category=None,
        top_k=5
    )
    
    assert isinstance(results, list)

