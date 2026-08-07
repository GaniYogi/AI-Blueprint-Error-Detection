from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "engine": "active"
    }
