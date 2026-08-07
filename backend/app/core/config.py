import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Blueprint Error Detection"
    API_V1_STR: str = "/api"
    
    # JWT Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super_secret_key_for_ai_blueprint_error_detection_app_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    REPORTS_DIR: Path = BASE_DIR / "reports"
    MODELS_DIR: Path = BASE_DIR / "models"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/backend/blueprint_error_detection.db")

    class Config:
        case_sensitive = True

settings = Settings()

# Create directories if they do not exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
(settings.BASE_DIR / "dataset").mkdir(parents=True, exist_ok=True)
(settings.BASE_DIR / "docs").mkdir(parents=True, exist_ok=True)
