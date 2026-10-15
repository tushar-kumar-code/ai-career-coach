# FastAPI Application Entrypoint - Auth & Terminal Logging Enabled
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AICareerCoachException
from app.core.logging_config import setup_terminal_logging
from app.api.router import api_router

# Setup rich colored terminal logging for the whole backend
setup_terminal_logging(level=logging.INFO)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables & seed data on startup
    logger.info("Initializing database schema & seed data...")
    try:
        import app.models
        from app.core.database import engine, Base, AsyncSessionLocal
        from app.core.init_db import seed_database

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as session:
            await seed_database(session)
        logger.info("✅ Database tables verified and seed data initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Error during database initialization: {e}", exc_info=True)

    yield
    logger.info("Shutting down AI Career Coach application.")


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


def get_route_tag(path: str) -> str:
    if "/assessment" in path: return "[ASSESSMENT]"
    if "/roadmap" in path: return "[ROADMAP]"
    if "/interview" in path: return "[INTERVIEW]"
    if "/resume" in path: return "[RESUME]"
    if "/jobs" in path: return "[JOBS]"
    if "/skills" in path: return "[SKILLS]"
    if "/digital-twin" in path: return "[DIGITAL TWIN]"
    if "/placement" in path: return "[PLACEMENT]"
    if "/chat" in path: return "[AI CHAT]"
    if "/auth" in path: return "[AUTH]"
    if "/settings" in path: return "[SETTINGS]"
    if "/health" in path: return "[HEALTH]"
    return "[API]"


# Terminal Live Request & Response Logger Middleware
@app.middleware("http")
async def terminal_http_logger_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    query = request.url.query
    query_str = f"?{query}" if query else ""
    client_ip = request.client.host if request.client else "unknown"

    # Avoid cluttering with internal client-log roundtrips or repetitive root checks
    is_client_log = "/client-log" in path
    is_root = path == "/"
    tag = get_route_tag(path)

    if not is_client_log and not is_root:
        # Check if auth header is present
        auth_header = request.headers.get("authorization")
        auth_tag = " [Authenticated]" if auth_header else ""
        lang = request.headers.get("x-language-preference", "en")
        logger.info(f"📥 {tag} [REQUEST] {method} {path}{query_str} (IP: {client_ip}{auth_tag} | Lang: {lang})")

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        status_code = response.status_code

        if not is_client_log and not is_root:
            if status_code < 400:
                logger.info(f"📤 {tag} [RESPONSE] {method} {path} -> {status_code} OK ({duration_ms:.1f}ms)")
            elif status_code < 500:
                logger.warning(f"⚠️  {tag} [CLIENT ERROR] {method} {path} -> {status_code} ({duration_ms:.1f}ms)")
            else:
                logger.error(f"❌ {tag} [SERVER ERROR] {method} {path} -> {status_code} ({duration_ms:.1f}ms)")

        return response
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"💥 {tag} [EXCEPTION] {method} {path} crashed after {duration_ms:.1f}ms: {exc}", exc_info=True)
        raise exc


# Exception Handlers
@app.exception_handler(AICareerCoachException)
async def domain_exception_handler(request: Request, exc: AICareerCoachException):
    logger.warning(f"⚠️  [DOMAIN ERROR] Handled {exc.__class__.__name__}: {exc.message}")
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
