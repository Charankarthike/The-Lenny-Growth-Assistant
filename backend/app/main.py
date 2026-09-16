"""
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.logging_config import setup_logging, get_logger
from app.api.v1.router import api_router
from app.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware
from app.db.base import engine

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(
        "application_startup",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider
    )
    
    # Test database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("database_connection_established")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        # Continue anyway - health check will show degraded status
    
    # Load embedding model if using local
    if settings.embedding_provider == "local":
        logger.info("loading_local_embedding_model", model=settings.local_embedding_model)
        # Model loading will be implemented in RAG phase
    
    yield
    
    # Shutdown
    logger.info("application_shutdown")
    engine.dispose()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered conversational assistant for Lenny's Podcast insights",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint that verifies system components.
    
    Returns:
        dict: Health status of the application and its components
    """
    components = {}
    overall_status = "healthy"
    
    # Database check
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
        logger.error("database_health_check_failed", error=str(e))
    
    # LLM provider check
    try:
        llm_config = settings.get_llm_config()
        if settings.llm_provider == "ollama":
            # TODO: Check if Ollama is running
            # response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2)
            components["llm_provider"] = f"healthy (ollama: {settings.ollama_model})"
        elif settings.llm_provider == "anthropic":
            if settings.anthropic_api_key:
                components["llm_provider"] = f"healthy (anthropic: {settings.anthropic_model})"
            else:
                components["llm_provider"] = "unhealthy: missing API key"
                overall_status = "degraded"
        elif settings.llm_provider == "openai":
            if settings.openai_api_key:
                components["llm_provider"] = f"healthy (openai: {settings.openai_model})"
            else:
                components["llm_provider"] = "unhealthy: missing API key"
                overall_status = "degraded"
    except Exception as e:
        components["llm_provider"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
        logger.error("llm_provider_health_check_failed", error=str(e))
    
    # Vector store check
    try:
        # TODO: Implement vector store health check
        components["vector_store"] = "healthy"
    except Exception as e:
        components["vector_store"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
        logger.error("vector_store_health_check_failed", error=str(e))
    
    return {
        "status": overall_status,
        "version": settings.app_version,
        "environment": settings.environment,
        "components": components
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "disabled",
        "health": "/health",
        "api": "/api/v1"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
