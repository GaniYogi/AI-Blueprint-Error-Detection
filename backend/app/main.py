from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal

from app.routers import (
    auth,
    blueprints,
    rules,
    analytics,
    settings as router_settings,
    compliance,
    health,
)

from app.routers.rules import init_default_rules


# -------------------------------------------------
# Database setup
# -------------------------------------------------

Base.metadata.create_all(bind=engine)


# Populate default compliance rules
db = SessionLocal()

try:
    init_default_rules(db)
finally:
    db.close()


# -------------------------------------------------
# FastAPI application
# -------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Full-stack AI-powered blueprint analysis engine "
        "and building code compliance checker."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# -------------------------------------------------
# CORS configuration
# -------------------------------------------------

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# API Routers
# -------------------------------------------------

app.include_router(
    auth.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    blueprints.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    rules.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    analytics.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    router_settings.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    compliance.router,
    prefix=settings.API_V1_STR,
)

app.include_router(
    health.router,
    prefix=settings.API_V1_STR,
)


# -------------------------------------------------
# Root endpoint
# -------------------------------------------------

@app.get("/")
def health_check():

    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "engine": "active",
    }


# -------------------------------------------------
# Run server directly
# -------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
