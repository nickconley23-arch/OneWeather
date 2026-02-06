"""
Health check endpoints
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "OneWeather API",
        "version": "0.1.0"
    }


@router.get("/system")
async def system_health():
    """System health information"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent,
        "process_id": os.getpid()
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check for load balancers"""
    # Add database connection check here when we have DB
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }