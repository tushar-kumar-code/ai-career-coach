import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
frontend_logger = logging.getLogger("frontend")


class ClientLogPayload(BaseModel):
    level: str = "info"  # "info", "action", "navigation", "api", "auth", "warn", "error"
    message: str
    route: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


@router.post("/client-log", include_in_schema=False)
async def log_frontend_event(payload: ClientLogPayload):
    """Receive client-side events from the frontend and display them in the terminal."""
    route_info = f" [{payload.route}]" if payload.route else ""
    details_str = f" | {payload.details}" if payload.details else ""
    lvl = (payload.level or "info").lower()

    if lvl == "error":
        frontend_logger.error(f"🚨 ERROR: {payload.message}{route_info}{details_str}")
    elif lvl in ["warn", "warning"]:
        frontend_logger.warning(f"⚠️  WARN: {payload.message}{route_info}{details_str}")
    elif lvl == "action":
        frontend_logger.info(f"⚡ ACTION: {payload.message}{route_info}{details_str}")
    elif lvl in ["nav", "navigation"]:
        frontend_logger.info(f"🧭 NAVIGATED: {payload.message}{details_str}")
    elif lvl == "api":
        frontend_logger.info(f"📡 {payload.message}{route_info}")
    elif lvl == "auth":
        frontend_logger.info(f"🔐 AUTH: {payload.message}{details_str}")
    else:
        frontend_logger.info(f"💻 {payload.message}{route_info}{details_str}")

    return {"status": "logged"}
