"""
Health check endpoints
"""
from fastapi import APIRouter, status
from datetime import datetime
from app.core import settings

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Basic health check endpoint"""
    from app.core.database import check_db_connection
    
    db_connected = check_db_connection()
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.app_name,
        "environment": settings.environment,
        "database": "connected" if db_connected else "disconnected",
    }


@router.get("/", status_code=status.HTTP_200_OK)
async def root():
    """Root endpoint"""
    return {
        "message": "Lenny Growth Assistant API",
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs",
    }
