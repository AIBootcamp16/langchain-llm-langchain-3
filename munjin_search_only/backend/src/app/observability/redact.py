"""
PII/민감정보 마스킹 규칙 (선택)
개인정보 보호를 위한 데이터 마스킹 유틸리티
"""

import re
from typing import Any, Dict


def redact_email(text: str) -> str:
    """
    이메일 주소 마스킹
    
    Args:
        text: 원본 텍스트
    
    Returns:
        str: 마스킹된 텍스트
    
    Example:
        >>> redact_email("user@example.com")
        "u***@example.com"
    """
    pattern = r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    
    def mask(match):
        username = match.group(1)
        domain = match.group(2)
        masked_username = username[0] + "***" if len(username) > 0 else "***"
        return f"{masked_username}@{domain}"
    
    return re.sub(pattern, mask, text)


def redact_phone(text: str) -> str:
    """
    전화번호 마스킹
    
    Args:
        text: 원본 텍스트
    
    Returns:
        str: 마스킹된 텍스트
    
    Example:
        >>> redact_phone("010-1234-5678")
        "010-****-5678"
    """
    pattern = r'(\d{2,3})-?(\d{3,4})-?(\d{4})'
    
    def mask(match):
        first = match.group(1)
        last = match.group(3)
        return f"{first}-****-{last}"
    
    return re.sub(pattern, mask, text)


def redact_resident_number(text: str) -> str:
    """
    주민등록번호 마스킹
    
    Args:
        text: 원본 텍스트
    
    Returns:
        str: 마스킹된 텍스트
    
    Example:
        >>> redact_resident_number("123456-1234567")
        "123456-*******"
    """
    pattern = r'(\d{6})-?(\d{7})'
    
    def mask(match):
        first = match.group(1)
        return f"{first}-*******"
    
    return re.sub(pattern, mask, text)


def redact_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    딕셔너리 내의 PII 정보 마스킹
    
    Args:
        data: 원본 데이터
    
    Returns:
        Dict[str, Any]: 마스킹된 데이터
    """
    if not isinstance(data, dict):
        return data
    
    redacted = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # 이메일 마스킹
            value = redact_email(value)
            # 전화번호 마스킹
            value = redact_phone(value)
            # 주민등록번호 마스킹
            value = redact_resident_number(value)
        elif isinstance(value, dict):
            # 재귀적으로 처리
            value = redact_pii(value)
        elif isinstance(value, list):
            # 리스트 내의 각 항목 처리
            value = [redact_pii(item) if isinstance(item, dict) else item for item in value]
        
        redacted[key] = value
    
    return redacted

