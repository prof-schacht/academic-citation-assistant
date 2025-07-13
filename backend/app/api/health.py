"""Health check endpoints."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from app.core.config import settings


router = APIRouter()


async def get_redis_client():
    """Get Redis client instance."""
    client = redis.from_url(
        settings.redis_url,
        password=settings.redis_password if settings.redis_password else None,
        decode_responses=True,
    )
    try:
        yield client
    finally:
        await client.close()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get("/ready")
async def readiness_check(
    redis_client: redis.Redis = Depends(get_redis_client),
) -> Dict[str, Any]:
    """
    Readiness probe to check if all services are ready.
    
    Checks:
    - Database connection (will be added when DB is set up)
    - Redis connection
    """
    response = {
        "status": "ready",
        "checks": {
            "redis": "unknown",
            "database": "not_implemented",
        }
    }
    
    # Check Redis connection
    try:
        await redis_client.ping()
        response["checks"]["redis"] = "healthy"
    except Exception as e:
        response["status"] = "not_ready"
        response["checks"]["redis"] = f"unhealthy: {str(e)}"
    
    # Database check will be added later when SQLAlchemy is configured
    
    if response["status"] == "not_ready":
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe to check if the application is running.
    
    This endpoint should always return 200 unless the application
    is in a completely broken state.
    """
    return {
        "status": "alive",
        "service": settings.app_name,
    }