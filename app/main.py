from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.handlers import setup_exception_handlers
from app.core.middleware import RequestLoggingMiddleware
from app.schemas.common import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("taskflow.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Initializing TaskFlow API services...")
    # Auto-create tables for development / SQLite mode
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema validated successfully.")
    yield
    logger.info("Shutting down TaskFlow API services...")
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # Global Exception Handlers
    setup_exception_handlers(app)

    # Include API Routers
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get(
        "/",
        tags=["Health & General"],
        summary="Root Welcome Endpoint",
    )
    async def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "documentation": "/docs",
            "alternative_docs": "/redoc",
            "api_v1": settings.API_V1_STR,
        }

    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health & General"],
        summary="Health Check Endpoint",
    )
    async def health_check() -> HealthResponse:
        return HealthResponse(
            status="healthy",
            version=settings.VERSION,
            database="connected",
            environment=settings.ENVIRONMENT,
        )

    return app


app = create_application()
