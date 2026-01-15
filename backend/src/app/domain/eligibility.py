"""
Eligibility Domain Models
자격 확인 관련 Pydantic 스키마 (체크리스트 방식 반영)
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class Condition(BaseModel):
    """개별 자격 조건 데이터 구조"""
    name: str = Field(..., description="조건명")
    description: Optional[str] = Field(None, description="조건 설명")
    # 14대 표준 카테고리 대응을 위해 유형 확장
    type: str = Field(..., description="조건 타입 (age, location, business_type 등)")
    value: Optional[str] = Field(None, description="조건 값 (예: 19~39세, 서울특별시)")
    status: Literal["UNKNOWN", "PASS", "FAIL"] = Field("UNKNOWN", description="판정 상태")
    reason: Optional[str] = Field(None, description="판정 사유")


class ChecklistItem(BaseModel):
    """UI 체크리스트 구성을 위한 항목"""
    condition_index: int = Field(..., description="조건 인덱스")
    label: str = Field(..., description="사용자에게 보여줄 문구")
    selection: Optional[Literal["PASS", "FAIL", "UNKNOWN"]] = Field(None, description="사용자 선택 값")


class EligibilityStartRequest(BaseModel):
    """자격 확인 시작 요청"""
    session_id: Optional[str] = Field(None, description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 35
            }
        }


class EligibilityStartResponse(BaseModel):
    """
    자격 확인 시작 응답 (설계서 p.8 반영)
    기존 question/progress 대신 checklist를 반환하도록 고도화
    """
    session_id: str = Field(..., description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    checklist: List[Dict[str, Any]] = Field(default_factory=list, description="추출된 조건 체크리스트")
    extra_requirements: Optional[str] = Field(None, description="기타 추가 요건 안내 문구")
    
    # 하위 호환성을 위해 Optional로 변경 (에러 해결 핵심)
    question: Optional[str] = Field(None, description="첫 번째 질문 (이전 방식용)")
    progress: Optional[dict] = Field(None, description="진행률 (이전 방식용)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 35,
                "checklist": [
                    {"condition_index": 0, "label": "연령: 19세~39세", "selection": None},
                    {"condition_index": 1, "label": "거주지: 서울특별시", "selection": None}
                ],
                "extra_requirements": "기타 상세 내용은 공고문을 참조해 주세요."
            }
        }


class EligibilityAnswerRequest(BaseModel):
    """자격 확인 결과 제출 요청 (submit 용으로 재사용 가능)"""
    session_id: str = Field(..., description="세션 ID")
    # 체크리스트 결과 리스트를 받도록 구성
    checklist_result: Optional[List[Dict[str, Any]]] = Field(None, description="사용자 선택 결과 목록")
    answer: Optional[str] = Field(None, description="사용자 답변 (이전 방식용)")


class ConditionResult(BaseModel):
    """최종 결과의 개별 조건 상세 판정"""
    condition: str = Field(..., description="조건명")
    status: str = Field(..., description="판정 결과 (PASS, FAIL, UNKNOWN)")
    reason: Optional[str] = Field("", description="판정 상세 사유")


class EligibilityResult(BaseModel):
    """
    최종 자격 판정 결과 (설계서 p.11 반영)
    """
    session_id: str = Field(..., description="세션 ID")
    policy_id: int = Field(..., description="정책 ID")
    # 결과 유형에 CANNOT_DETERMINE 추가
    result: Literal["ELIGIBLE", "NOT_ELIGIBLE", "CANNOT_DETERMINE"] = Field(..., description="최종 결과")
    reason: str = Field(..., description="종합 판정 사유 및 문의처 안내")
    details: List[ConditionResult] = Field(..., description="조건별 상세 결과")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "policy_id": 35,
                "result": "CANNOT_DETERMINE",
                "reason": "세부 요건 확인이 필요합니다. 문의처(02-123-4567)로 전화하여 확인해 주세요.",
                "details": [
                    {"condition": "연령", "status": "PASS", "reason": "만 25세로 조건 충족"},
                    {"condition": "기타", "status": "UNKNOWN", "reason": "추가 확인 필요"}
                ]
            }
        }