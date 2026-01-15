"""
FastAPI Application Entrypoint
정책·지원금 AI Agent의 메인 애플리케이션
"""

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
    if settings.langsmith_tracing and settings.langsmith_api_key:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint

        # LangSmith 클라이언트 초기화 (캐싱된 인스턴스 미리 생성)
        from .observability import get_langsmith_client
        langsmith_client = get_langsmith_client()

        logger.info(
            "LangSmith tracing enabled",
            extra={
                "project": settings.langsmith_project,
                "endpoint": settings.langsmith_endpoint,
                "client_initialized": langsmith_client.is_enabled()
            }
        )
    else:
        logger.info("LangSmith tracing is disabled (no API key or tracing=false)")
    
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

# API v1 routes (기본)
app.include_router(routes_policy.router, prefix="/api/v1", tags=["Policies v1"])
app.include_router(routes_chat.router, prefix="/api/v1", tags=["Chat v1"])
app.include_router(routes_eligibility.router, prefix="/api/v1", tags=["Eligibility v1"])
app.include_router(routes_admin.router, prefix="/api/v1", tags=["Admin v1"])

# API routes (frontend 호환성 - /api prefix)
app.include_router(routes_policy.router, prefix="/api", tags=["Policies"])
app.include_router(routes_chat.router, prefix="/api", tags=["Chat"])
app.include_router(routes_eligibility.router, prefix="/api", tags=["Eligibility"])
app.include_router(routes_admin.router, prefix="/api", tags=["Admin"])

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

