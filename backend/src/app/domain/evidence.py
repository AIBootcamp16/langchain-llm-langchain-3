"""
Evidence Domain Models
근거 관련 Pydantic 스키마
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field
from enum import Enum


class EvidenceType(str, Enum):
    """근거 타입"""
    INTERNAL = "internal"  # 내부 정책 문서
    WEB = "web"  # 웹 검색 결과


class Evidence(BaseModel):
    """근거 정보"""
    
    type: EvidenceType = Field(..., description="근거 타입")
    source: str = Field(..., description="출처")
    content: str = Field(..., description="내용")
    url: Optional[str] = Field(None, description="URL (웹 검색인 경우)")
    fetched_date: Optional[date] = Field(None, description="조회일 (웹 검색인 경우)")
    score: Optional[float] = Field(None, description="관련도 점수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "type": "internal",
                "source": "정책 문서 섹션 3",
                "content": "지원 금액은 최대 0.8억원입니다.",
                "score": 0.95
            }
        }

