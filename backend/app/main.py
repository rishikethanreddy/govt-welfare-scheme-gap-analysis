"""
FastAPI application factory.

This is the main entry point for the backend application.
Run with: uvicorn backend.app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.database import Base, engine
from backend.app.middleware.error_handler import ErrorHandlerMiddleware, RequestLoggingMiddleware

# Import all models so they are registered with Base.metadata
from backend.app.models import (  # noqa: F401
    Document, Scheme, Source, SourceRun,
    DatasetVersion, ProcessingJob, Cluster, DocumentCluster,
    GeographicEntity, ModelVersion, AuditLog,
)

# Import routers
from backend.app.routers import (
    health, dashboard, documents, schemes,
    geography, sources, datasets, analyze,
    models_api, system, collection,
)

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Database: {'SQLite' if settings.is_sqlite else 'PostgreSQL'}")

    # Create tables if they don't exist (dev convenience)
    # In production, use Alembic migrations instead.
    if not settings.is_production:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")

    yield

    # Shutdown
    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Government Welfare Scheme Awareness Gap Miner",
        description=(
            "An analytical platform for ingesting public textual data about Indian "
            "government welfare schemes, identifying awareness gaps, and presenting "
            "geographic and thematic intelligence through interactive dashboards.\n\n"
            "**Academic Research Prototype** — All analytical results originate from "
            "actual stored data. This system does not fabricate statistics or conclusions."
        ),
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── Middleware ─────────────────────────────────────────────────────────
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(documents.router)
    app.include_router(schemes.router)
    app.include_router(geography.router)
    app.include_router(sources.router)
    app.include_router(datasets.router)
    app.include_router(analyze.router)
    app.include_router(models_api.router)
    app.include_router(system.router)
    app.include_router(collection.router)

    # ── Root Redirect ─────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/health",
        }

    return app


# Application instance
app = create_app()
