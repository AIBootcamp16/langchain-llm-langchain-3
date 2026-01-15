"""
Admin API Routes
관리자 및 헬스체크 엔드포인트
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.engine import get_db_session
from ..vector_store import get_qdrant_manager
from ..config import get_settings
from ..config.logger import get_logger

logger = get_logger()
settings = get_settings()
router = APIRouter()


@router.get(
    "/health",
    summary="헬스체크",
    description="서비스 상태를 확인합니다.",
    tags=["Admin"]
)
async def health_check():
    """
    헬스체크 엔드포인트
    
    컨테이너 및 로드밸런서 헬스체크용
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get(
    "/health/db",
    summary="데이터베이스 헬스체크",
    description="MySQL 연결 상태를 확인합니다.",
    tags=["Admin"]
)
async def db_health_check(db: Session = Depends(get_db_session)):
    """
    데이터베이스 헬스체크
    
    MySQL 연결 확인
    """
    try:
        # Execute simple query
        from ..db.models import Policy
        count = db.query(Policy).count()
        
        return {
            "status": "healthy",
            "database": "mysql",
            "policies_count": count
        }
    except Exception as e:
        logger.error("Database health check failed", extra={"error": str(e)}, exc_info=True)
        return {
            "status": "unhealthy",
            "database": "mysql",
            "error": str(e)
        }


@router.get(
    "/health/qdrant",
    summary="Qdrant 헬스체크",
    description="Qdrant 연결 상태를 확인합니다.",
    tags=["Admin"]
)
async def qdrant_health_check():
    """
    Qdrant 헬스체크
    
    Qdrant 컬렉션 정보 확인
    """
    try:
        qdrant_manager = get_qdrant_manager()
        info = qdrant_manager.get_collection_info()
        
        return {
            "status": "healthy",
            "vectordb": "qdrant",
            **info
        }
    except Exception as e:
        logger.error("Qdrant health check failed", extra={"error": str(e)}, exc_info=True)
        return {
            "status": "unhealthy",
            "vectordb": "qdrant",
            "error": str(e)
        }


@router.get(
    "/stats",
    summary="서비스 통계",
    description="서비스 전반적인 통계를 조회합니다.",
    tags=["Admin"]
)
async def get_stats(db: Session = Depends(get_db_session)):
    """
    서비스 통계 조회
    
    정책, 세션, 채팅 이력 등의 통계
    """
    try:
        from ..db.models import Policy, Session as DBSession, ChatHistory
        
        policies_count = db.query(Policy).count()
        sessions_count = db.query(DBSession).count()
        chats_count = db.query(ChatHistory).count()
        
        # Region distribution
        from sqlalchemy import func
        region_dist = db.query(
            Policy.region,
            func.count(Policy.id)
        ).group_by(Policy.region).all()
        
        # Category distribution
        category_dist = db.query(
            Policy.category,
            func.count(Policy.id)
        ).group_by(Policy.category).all()
        
        return {
            "policies": {
                "total": policies_count,
                "by_region": {r[0]: r[1] for r in region_dist if r[0]},
                "by_category": {c[0]: c[1] for c in category_dist if c[0]}
            },
            "sessions": {
                "total": sessions_count
            },
            "chats": {
                "total": chats_count
            }
        }
        
    except Exception as e:
        logger.error("Error getting stats", extra={"error": str(e)}, exc_info=True)
        return {"error": str(e)}

