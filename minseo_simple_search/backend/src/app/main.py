"""
FastAPI Application Entrypoint
정책·지원금 AI Agent의 메인 애플리케이션
"""
# ==============================================================================
# Monkey patch for langchain_core.pydantic_v1 compatibility
# This should be at the very top before any other imports that might use LangChain
# ==============================================================================
import sys
try:
    import pydantic.v1 as pydantic_v1
    sys.modules['langchain_core.pydantic_v1'] = pydantic_v1
except ImportError:
    # If pydantic.v1 is not available, we can't apply the patch.
    # This might happen with very old or very new versions of pydantic.
    pass
# ==============================================================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .config.logger import get_logger
from .db.engine import init_db, close_db
from .api import routes_policy, routes_admin, routes_chat, routes_eligibility, routes_web_source

# Initialize
settings = get_settings()
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan context manager
    시작 시 DB 연결, 종료 시 리소스 정리
    """
    logger.info("Starting application", extra={"environment": settings.environment})
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    # Initialize LangSmith (if enabled)
    if settings.langsmith_tracing:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key or ""
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        logger.info("LangSmith tracing enabled", extra={"project": settings.langsmith_project})
    
    yield
    
    # Cleanup
    logger.info("Shutting down application")
    close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="정부 정책·지원금 정보를 쉽게 탐색하고, 근거 기반 설명 + 자격 가능성 판단을 제공하는 AI 에이전트",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health Check Endpoints
# ============================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    컨테이너 헬스체크용 엔드포인트
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": settings.app_name,
            "environment": settings.environment,
        }
    )


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint
    API 기본 정보 제공
    """
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
    }


# ============================================================
# Include Routers
# ============================================================

app.include_router(routes_policy.router, prefix="/api/v1/policies", tags=["Policies"])
app.include_router(routes_chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(routes_eligibility.router, prefix="/api/v1/eligibility", tags=["Eligibility"])
app.include_router(routes_admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(routes_web_source.router)


# ============================================================
# Exception Handlers
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error": str(exc),
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred",
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
