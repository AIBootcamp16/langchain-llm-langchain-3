"""
Pytest Configuration
테스트 설정 및 픽스처
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.app.main import app
from src.app.db.engine import get_db
from src.app.db.models import Base


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Create test database
    각 테스트마다 새로운 DB 생성
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create test client
    FastAPI 테스트 클라이언트 생성
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_policy_data():
    """샘플 정책 데이터"""
    return {
        "program_id": "TEST001",
        "region": "서울",
        "category": "창업",
        "program_name": "테스트 창업 지원 프로그램",
        "support_description": "예비창업자를 위한 자금 지원",
        "apply_target": "예비창업자(사업자 등록 전)",
        "support_details": "최대 5000만원 지원",
        "apply_method": "온라인 신청",
        "contact": "02-1234-5678",
        "url": "https://example.com"
    }


@pytest.fixture
def sample_chat_request():
    """샘플 채팅 요청"""
    return {
        "session_id": "test-session-001",
        "message": "창업 지원금에 대해 알려주세요",
        "policy_id": 1
    }


@pytest.fixture
def sample_eligibility_request():
    """샘플 자격 확인 요청"""
    return {
        "policy_id": 1
    }

