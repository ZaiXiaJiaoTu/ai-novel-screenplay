from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.response import fail, success

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("")
def health_check():
    return success(
        {
            "status": "ok",
            "service": settings.app_name,
            "version": settings.app_version,
        }
    )


@router.get("/db")
def database_health_check():
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        return JSONResponse(
            status_code=503,
            content=fail(
                "database connection failed",
                code=503,
                data={"status": "error", "detail": str(exc)},
            ),
        )
    return success({"status": "ok"})
