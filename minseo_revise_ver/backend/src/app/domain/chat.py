"""
Chat Domain Models
채팅 관련 Pydantic 스키마
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .evidence import Evidence


class ChatRequest(BaseModel):
    """채팅 요청"""
    
    session_id: Optional[str] = Field(None, description="세션 ID (없으면 자동 생성)")
    policy_id: int = Field(..., description="정책 ID")
    message: str = Field(..., min_length=1, description="사용자 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 1,
                "message": "이 정책 신청 마감일이 언제야?"
            }
        }


class ChatResponse(BaseModel):
    """채팅 응답"""
    
    session_id: str = Field(..., description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    answer: str = Field(..., description="AI 답변")
    evidence: List[Evidence] = Field(default_factory=list, description="근거 목록")
    error: Optional[str] = Field(None, description="에러 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 1,
                "answer": "예비창업패키지는 '26년 1~2월에 신청·접수 예정입니다.",
                "evidence": [
                    {
                        "type": "internal",
                        "source": "정책 문서 (섹션: process)",
                        "content": "사업공고('25.12월),신청·접수('26.1~2월 예정)...",
                        "score": 0.92
                    }
                ]
            }
        }


class SessionResetResponse(BaseModel):
    """세션 초기화 응답"""
    
    session_id: str = Field(..., description="세션 ID")
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "success": True,
                "message": "세션이 초기화되었습니다."
            }
        }

