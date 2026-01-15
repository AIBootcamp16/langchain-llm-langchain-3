"""
Policy Domain Models
정책 관련 Pydantic 스키마
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field


class PolicySearchRequest(BaseModel):
    """정책 검색 요청"""
    
    query: Optional[str] = Field(None, description="검색 쿼리")
    region: Optional[str] = Field(None, description="지역 필터")
    category: Optional[str] = Field(None, description="카테고리 필터")
    limit: int = Field(10, ge=1, le=100, description="반환 개수")
    offset: int = Field(0, ge=0, description="오프셋")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "서울 창업 지원금",
                "region": "서울",
                "category": "사업화",
                "limit": 10,
                "offset": 0
            }
        }


class PolicyResponse(BaseModel):
    """정책 응답"""
    
    id: int = Field(..., description="정책 고유 ID")
    program_id: int = Field(..., description="프로그램 ID")
    region: Optional[str] = Field(None, description="지역")
    category: Optional[str] = Field(None, description="카테고리")
    program_name: str = Field(..., description="정책명")
    program_overview: Optional[str] = Field(None, description="정책 개요")
    support_description: Optional[str] = Field(None, description="지원 내용")
    support_budget: Optional[int] = Field(None, description="지원 예산 (원)")
    support_scale: Optional[str] = Field(None, description="지원 규모")
    supervising_ministry: Optional[str] = Field(None, description="주관 부처")
    apply_target: Optional[str] = Field(None, description="신청 대상")
    announcement_date: Optional[str] = Field(None, description="공고일")
    biz_process: Optional[str] = Field(None, description="사업 프로세스")
    application_method: Optional[str] = Field(None, description="신청 방법")
    contact_agency: Optional[List[str]] = Field(None, description="문의처")
    contact_number: Optional[List[str]] = Field(None, description="연락처")
    required_documents: Optional[List[str]] = Field(None, description="필요 서류")
    collected_date: Optional[date] = Field(None, description="수집일")
    created_at: Optional[datetime] = Field(None, description="생성일")
    
    # Search metadata (optional)
    score: Optional[float] = Field(None, description="검색 스코어")
    
    # Web search metadata (optional)
    screenshot_url: Optional[str] = Field(None, description="웹사이트 스크린샷 URL")
    favicon_url: Optional[str] = Field(None, description="웹사이트 파비콘 URL")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "program_id": 1,
                "region": "전국",
                "category": "사업화",
                "program_name": "예비창업패키지",
                "program_overview": "혁신적인 기술창업 아이디어를 보유한...",
                "support_description": "사업화자금, 창업프로그램등...",
                "support_budget": 49125000000,
                "support_scale": "750명내외",
                "supervising_ministry": "중소벤처기업부",
                "apply_target": "예비창업자",
                "announcement_date": "'25. 12~'26. 1월(예정)",
                "score": 0.95
            }
        }


class PolicyListResponse(BaseModel):
    """정책 리스트 응답"""
    
    total: int = Field(..., description="전체 개수")
    count: int = Field(..., description="현재 개수")
    offset: int = Field(..., description="오프셋")
    limit: int = Field(..., description="제한")
    policies: List[PolicyResponse] = Field(..., description="정책 리스트")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 508,
                "count": 10,
                "offset": 0,
                "limit": 10,
                "policies": [
                    {
                        "id": 1,
                        "program_id": 1,
                        "program_name": "예비창업패키지",
                        "region": "전국",
                        "category": "사업화"
                    }
                ]
            }
        }

