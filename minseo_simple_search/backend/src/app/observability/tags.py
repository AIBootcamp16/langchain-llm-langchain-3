"""
Run Tags 관리
실행 환경, 기능, 정책 ID 등의 태그를 생성합니다.
"""

from typing import Optional
import os

from ..config import get_settings


def get_base_tags() -> list[str]:
    """
    기본 태그 반환
    
    Returns:
        list[str]: 기본 태그 리스트 (environment)
    
    Example:
        >>> get_base_tags()
        ['env:development']
    """
    settings = get_settings()
    return [f"env:{settings.environment}"]


def get_feature_tags(
    feature: str, 
    policy_id: Optional[int] = None,
    additional_tags: Optional[list[str]] = None
) -> list[str]:
    """
    기능별 태그 생성
    
    Args:
        feature: 기능 코드
            - "PS": Policy Search (정책 검색)
            - "QA": Q&A (정책 질의응답)
            - "EC": Eligibility Check (자격 확인)
        policy_id: 정책 ID (선택)
        additional_tags: 추가 태그 (선택)
    
    Returns:
        list[str]: 태그 리스트
    
    Example:
        >>> get_feature_tags("QA", policy_id=1)
        ['env:development', 'feature:QA', 'policy:1']
    """
    tags = get_base_tags()
    
    # Add feature tag
    feature_map = {
        "PS": "Policy-Search",
        "QA": "Q&A",
        "EC": "Eligibility-Check"
    }
    feature_name = feature_map.get(feature, feature)
    tags.append(f"feature:{feature_name}")
    
    # Add policy ID if provided
    if policy_id is not None:
        tags.append(f"policy:{policy_id}")
    
    # Add additional tags
    if additional_tags:
        tags.extend(additional_tags)
    
    return tags


def get_workflow_tags(
    workflow_type: str,
    session_id: Optional[str] = None,
    policy_id: Optional[int] = None
) -> list[str]:
    """
    워크플로우별 태그 생성
    
    Args:
        workflow_type: 워크플로우 타입 (search, qa, eligibility)
        session_id: 세션 ID (선택)
        policy_id: 정책 ID (선택)
    
    Returns:
        list[str]: 태그 리스트
    
    Example:
        >>> get_workflow_tags("qa", session_id="abc-123", policy_id=1)
        ['env:development', 'workflow:qa', 'session:abc-123', 'policy:1']
    """
    tags = get_base_tags()
    
    # Add workflow type
    tags.append(f"workflow:{workflow_type}")
    
    # Add session ID if provided
    if session_id:
        tags.append(f"session:{session_id[:8]}")  # 첫 8자만 사용
    
    # Add policy ID if provided
    if policy_id is not None:
        tags.append(f"policy:{policy_id}")
    
    return tags

