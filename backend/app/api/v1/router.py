"""
Main API router that aggregates all v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1 import config, sessions, messages, retrieval

api_router = APIRouter()

# Include sub-routers
api_router.include_router(config.router, prefix="/config", tags=["Configuration"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
api_router.include_router(messages.router, tags=["Messages"])
api_router.include_router(retrieval.router, prefix="/retrieval", tags=["Retrieval"])
