from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AICareerCoachException
from app.api.router import api_router

from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables & seed data on startup
    try:
        import app.models
        from app.core.database import engine, Base, AsyncSessionLocal
        from app.core.init_db import seed_database
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        async with AsyncSessionLocal() as session:
            await seed_database(session)
        logger.info("Database initialized and seeded successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-grade AI Career Coach API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
origins = [str(o).strip() for o in settings.BACKEND_CORS_ORIGINS if str(o).strip()]
if "*" in origins or not origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origin_regex=r"https://.*\.onrender\.com|http://localhost:\d+",
    )

# Exception Handlers
@app.exception_handler(AICareerCoachException)
async def domain_exception_handler(request: Request, exc: AICareerCoachException):
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": exc.message, "error": exc.__class__.__name__}
    )

# Mount API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "title": settings.PROJECT_NAME,
        "status": "running",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health"
    }
