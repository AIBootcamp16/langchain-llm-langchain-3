"""
Eligibility Domain Models
자격 확인 관련 Pydantic 스키마
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Condition(BaseModel):
    """자격 조건"""
    
    name: str = Field(..., description="조건명")
    description: str = Field(..., description="조건 설명")
    type: Literal["age", "region", "business_status", "industry", "other"] = Field(..., description="조건 타입")
    value: Optional[str] = Field(None, description="조건 값")
    status: Literal["UNKNOWN", "PASS", "FAIL"] = Field("UNKNOWN", description="판정 상태")
    reason: Optional[str] = Field(None, description="판정 사유")


class EligibilityStartRequest(BaseModel):
    """자격 확인 시작 요청"""
    
    session_id: Optional[str] = Field(None, description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 1
            }
        }


class EligibilityStartResponse(BaseModel):
    """자격 확인 시작 응답"""
    
    session_id: str = Field(..., description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    question: str = Field(..., description="첫 번째 질문")
    progress: dict = Field(..., description="진행률 {'current': 1, 'total': 5}")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 1,
                "question": "귀하의 사업자 등록 상태를 알려주세요. (예비창업자 / 창업 3년 이내 / 기타)",
                "progress": {"current": 1, "total": 3}
            }
        }


class EligibilityAnswerRequest(BaseModel):
    """자격 확인 답변 요청"""
    
    session_id: str = Field(..., description="세션 ID")
    answer: str = Field(..., min_length=1, description="사용자 답변")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "answer": "예비창업자입니다"
            }
        }


class EligibilityAnswerResponse(BaseModel):
    """자격 확인 답변 응답"""
    
    session_id: str = Field(..., description="세션 ID")
    question: Optional[str] = Field(None, description="다음 질문 (있는 경우)")
    progress: dict = Field(..., description="진행률")
    completed: bool = Field(False, description="완료 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "question": "거주 지역을 알려주세요.",
                "progress": {"current": 2, "total": 3},
                "completed": False
            }
        }


class ConditionResult(BaseModel):
    """조건별 판정 결과"""
    
    condition: str = Field(..., description="조건명")
    status: Literal["PASS", "FAIL", "UNKNOWN"] = Field(..., description="판정 결과")
    reason: str = Field(..., description="판정 사유")


class EligibilityResult(BaseModel):
    """최종 자격 판정 결과"""
    
    session_id: str = Field(..., description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    result: Literal["ELIGIBLE", "NOT_ELIGIBLE", "PARTIALLY"] = Field(..., description="최종 결과")
    reason: str = Field(..., description="종합 판정 사유")
    details: List[ConditionResult] = Field(..., description="조건별 상세 결과")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 1,
                "result": "ELIGIBLE",
                "reason": "모든 자격 조건을 충족합니다.",
                "details": [
                    {
                        "condition": "사업자 등록 상태",
                        "status": "PASS",
                        "reason": "예비창업자 조건을 만족합니다."
                    },
                    {
                        "condition": "지역",
                        "status": "PASS",
                        "reason": "전국 대상 정책으로 지역 제한이 없습니다."
                    }
                ]
            }
        }

