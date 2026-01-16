"""
Eligibility API Routes
자격 확인 API 라우터
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..config.logger import get_logger
from ..db.engine import get_db_session
from ..db.models import Policy, ChecklistResult, Session as DBSession, WorkflowTypeEnum
from ..domain.eligibility import (
    EligibilityStartRequest,
    EligibilityStartResponse,
    EligibilityAnswerRequest,
    EligibilityAnswerResponse,
    EligibilityResult,
    ConditionResult
)
from ..agent.workflows.eligibility_workflow import (
    run_eligibility_start,
    run_eligibility_answer
)
import uuid
from datetime import datetime

router = APIRouter(prefix="/eligibility", tags=["eligibility"])
logger = get_logger()

# In-memory session store (should use Redis in production)
_eligibility_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/start", response_model=EligibilityStartResponse)
async def start_eligibility_check(
    request: EligibilityStartRequest,
    db: Session = Depends(get_db_session)
):
    """
    자격 확인 시작
    
    Args:
        request: 자격 확인 시작 요청
        db: DB 세션
    
    Returns:
        EligibilityStartResponse: 첫 번째 질문 포함
    """
    try:
        # Get policy
        policy = db.query(Policy).filter(Policy.id == request.policy_id).first()
        if not policy:
            raise HTTPException(status_code=404, detail="정책을 찾을 수 없습니다.")
        
        if not policy.apply_target:
            raise HTTPException(status_code=400, detail="정책에 신청 대상 정보가 없습니다.")
        
        # Generate session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Run workflow
        result = run_eligibility_start(
            session_id=session_id,
            policy_id=request.policy_id,
            apply_target=policy.apply_target
        )
        
        # Save session to DB
        db_session = DBSession(
            id=session_id,
            policy_id=request.policy_id,
            workflow_type=WorkflowTypeEnum.ELIGIBILITY
        )
        db.add(db_session)
        db.commit()

        # Save session to memory
        _eligibility_sessions[session_id] = result
        
        # Calculate progress
        conditions = result.get("conditions", [])
        total_conditions = len(conditions)
        current_index = result.get("current_condition_index", 0)
        
        logger.info(
            "Eligibility check started",
            extra={
                "session_id": session_id,
                "policy_id": request.policy_id,
                "total_conditions": total_conditions
            }
        )
        
        return EligibilityStartResponse(
            session_id=session_id,
            policy_id=request.policy_id,
            question=result.get("current_question", "질문을 생성할 수 없습니다."),
            progress={
                "current": current_index + 1,
                "total": total_conditions
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error starting eligibility check",
            extra={"error": str(e), "policy_id": request.policy_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"자격 확인 시작 실패: {str(e)}")


@router.post("/answer", response_model=EligibilityAnswerResponse)
async def answer_eligibility_question(
    request: EligibilityAnswerRequest
):
    """
    자격 확인 질문 답변

    Args:
        request: 자격 확인 답변 요청

    Returns:
        EligibilityAnswerResponse: 다음 질문 또는 완료 메시지
    """
    try:
        # Get session
        session_id = request.session_id
        if session_id not in _eligibility_sessions:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")

        current_state = _eligibility_sessions[session_id]

        # DEBUG: Log incoming answer and session state
        print(f"[DEBUG] /answer endpoint called")
        print(f"  - session_id: {session_id}")
        print(f"  - user_answer: {request.answer}")
        print(f"  - current_condition_index: {current_state.get('current_condition_index')}")
        print(f"  - current_question: {current_state.get('current_question')}")
        print(f"  - existing user_slots: {current_state.get('user_slots', {})}")
        
        # Run workflow with answer
        result = run_eligibility_answer(
            session_id=session_id,
            user_answer=request.answer,
            current_state=current_state
        )
        
        # Update session
        _eligibility_sessions[session_id] = result

        # DEBUG: Log updated session state after processing
        print(f"[DEBUG] After processing answer:")
        print(f"  - updated user_slots: {result.get('user_slots', {})}")
        print(f"  - conditions: {result.get('conditions', [])}")

        # Calculate progress
        conditions = result.get("conditions", [])
        total_conditions = len(conditions)
        current_index = result.get("current_condition_index", 0)
        completed = result.get("completed", False)
        
        logger.info(
            "Eligibility answer processed",
            extra={
                "session_id": session_id,
                "completed": completed,
                "progress": f"{current_index}/{total_conditions}"
            }
        )
        
        return EligibilityAnswerResponse(
            session_id=session_id,
            question=result.get("current_question") if not completed else None,
            progress={
                "current": min(current_index, total_conditions),
                "total": total_conditions
            },
            completed=completed
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error processing eligibility answer",
            extra={"error": str(e), "session_id": request.session_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"답변 처리 실패: {str(e)}")


@router.get("/result/{session_id}", response_model=EligibilityResult)
async def get_eligibility_result(
    session_id: str,
    db: Session = Depends(get_db_session)
):
    """
    자격 확인 최종 결과 조회
    
    Args:
        session_id: 세션 ID
        db: DB 세션
    
    Returns:
        EligibilityResult: 최종 자격 판정 결과
    """
    try:
        # Get session
        if session_id not in _eligibility_sessions:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        state = _eligibility_sessions[session_id]
        
        # Check if completed
        if not state.get("completed", False):
            raise HTTPException(status_code=400, detail="자격 확인이 아직 완료되지 않았습니다.")
        
        # Build result
        conditions = state.get("conditions", [])
        condition_results = [
            ConditionResult(
                condition=c.get("name"),
                status=c.get("status"),
                reason=c.get("reason", "")
            )
            for c in conditions
        ]
        
        final_result = state.get("final_result", "NOT_ELIGIBLE")
        reason = state.get("reason", "")
        policy_id = state.get("policy_id")
        
        # Save to DB
        checklist_result = ChecklistResult(
            session_id=session_id,
            policy_id=policy_id,
            result=final_result,
            reason=reason,
            created_at=datetime.utcnow()
        )
        db.add(checklist_result)
        db.commit()
        
        logger.info(
            "Eligibility result retrieved",
            extra={
                "session_id": session_id,
                "result": final_result
            }
        )
        
        return EligibilityResult(
            session_id=session_id,
            policy_id=policy_id,
            result=final_result,
            reason=reason,
            details=condition_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting eligibility result",
            extra={"error": str(e), "session_id": session_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"결과 조회 실패: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_eligibility_session(session_id: str):
    """
    자격 확인 세션 삭제
    
    Args:
        session_id: 세션 ID
    
    Returns:
        dict: 성공 메시지
    """
    try:
        if session_id in _eligibility_sessions:
            del _eligibility_sessions[session_id]
            logger.info("Eligibility session deleted", extra={"session_id": session_id})
            return {"message": "세션이 삭제되었습니다.", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error deleting eligibility session",
            extra={"error": str(e), "session_id": session_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"세션 삭제 실패: {str(e)}")

