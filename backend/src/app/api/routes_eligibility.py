"""
Eligibility API Routes
자격 확인 API 라우터 (세션 무결성 및 워크플로우 타입 지정 버전)
"""

from typing import Dict, Any, List
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..config.logger import get_logger
from ..db.engine import get_db_session
# WorkflowTypeEnum을 추가로 임포트합니다.
from ..db.models import Policy, ChecklistResult, Session as SessionModel, WorkflowTypeEnum 
from ..domain.eligibility import (
    EligibilityStartRequest,
    EligibilityStartResponse,
    EligibilityResult,
    ConditionResult
)
from ..agent.workflows.eligibility_workflow import (
    run_eligibility_start,
    run_eligibility_result
)

router = APIRouter(prefix="/eligibility", tags=["eligibility"])
logger = get_logger()

# 서버 재시작 시 초기화되지만, 워크플로우 진행 중 상태 유지를 위한 In-memory store
_eligibility_sessions: Dict[str, Dict[str, Any]] = {}

@router.post("/start", response_model=EligibilityStartResponse)
async def start_eligibility_check(
    request: EligibilityStartRequest,
    db: Session = Depends(get_db_session)
):
    """
    자격 확인 시작: 실제 세션을 생성하고 workflow_type을 지정하여 DB에 기록합니다.
    """
    try:
        # 1. 정책 존재 여부 확인
        policy = db.query(Policy).filter(Policy.id == request.policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다.")
        
        # 2. 고유 세션 ID 생성 및 DB 저장
        # "Column 'workflow_type' cannot be null" 에러를 해결하기 위해 타입을 지정합니다.
        session_id = str(uuid.uuid4())
        
        new_session = SessionModel(
            id=session_id,
            policy_id=request.policy_id,
            workflow_type=WorkflowTypeEnum.ELIGIBILITY, # 자격 검증 워크플로우임을 명시
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_session)
        db.commit() # 부모 행(sessions)을 먼저 확정하여 외래 키 제약 조건을 충족합니다.

        # 3. 에이전트 워크플로우 실행 (체크리스트 생성)
        result = run_eligibility_start(
            session_id=session_id,
            policy_id=request.policy_id,
            apply_target=policy.apply_target or ""
        )
        
        if "error" in result and result["error"]:
            raise Exception(result["error"])

        # 4. 메모리에 현재 상태 저장 (다음 /submit 단계에서 사용)
        _eligibility_sessions[session_id] = result
        
        return EligibilityStartResponse(
            session_id=session_id,
            policy_id=request.policy_id,
            checklist=result.get("checklist", []),
            extra_requirements=result.get("extra_requirements")
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting eligibility check: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"자격 확인 시작 실패: {str(e)}")

@router.post("/submit", response_model=EligibilityResult)
async def submit_eligibility_results(
    session_id: str,
    checklist_result: List[Dict[str, Any]],
    db: Session = Depends(get_db_session)
):
    """
    체크리스트 결과 제출: 저장된 세션을 찾아 최종 판정을 내리고 DB에 저장합니다.
    """
    try:
        # 1. 메모리에서 세션 상태 확인
        if session_id not in _eligibility_sessions:
            logger.warning(f"Session not found in memory: {session_id}")
            raise HTTPException(status_code=404, detail="유효하지 않거나 만료된 세션입니다. 다시 시작해주세요.")
        
        current_state = _eligibility_sessions[session_id]
        
        # 2. 최종 판정 워크플로우 실행
        result = run_eligibility_result(
            session_id=session_id,
            checklist_result=checklist_result,
            current_state=current_state
        )
        
        # 3. DB 저장 (models.py 수정으로 CANNOT_DETERMINE 등 긴 문자열 저장 가능)
        final_result = result.get("final_result", "CANNOT_DETERMINE")
        reason = result.get("reason", "")
        
        db_result = ChecklistResult(
            session_id=session_id,
            policy_id=current_state.get("policy_id"),
            result=final_result,
            reason=reason,
            created_at=datetime.utcnow()
        )
        db.add(db_result)
        db.commit()
        
        # 4. 결과 반환
        return EligibilityResult(
            session_id=session_id,
            policy_id=current_state.get("policy_id"),
            result=final_result,
            reason=reason,
            details=[
                ConditionResult(
                    condition=c.get("name", "알 수 없는 조건"),
                    status=c.get("status", "UNKNOWN"),
                    reason=c.get("reason", "")
                ) for c in result.get("conditions", [])
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting eligibility results: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"결과 제출 실패: {str(e)}")