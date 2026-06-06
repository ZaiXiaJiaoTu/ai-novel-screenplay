from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.response import fail
from app.routers.book_router import router as book_router
from app.routers.chapter_router import router as chapter_router
from app.routers.health_router import router as health_router
from app.routers.llm_config_router import router as llm_config_router
from app.routers.llm_log_router import router as llm_log_router
from app.routers.prompt_template_router import router as prompt_template_router
from app.routers.script_adaptation_router import router as script_adaptation_router


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(book_router)
app.include_router(chapter_router)
app.include_router(script_adaptation_router)
app.include_router(llm_config_router)
app.include_router(prompt_template_router)
app.include_router(llm_log_router)
app.include_router(health_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=fail(str(exc.detail), code=exc.status_code),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=fail("请求参数校验失败", code=422, data=exc.errors()),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    detail = str(exc) if settings.env != "production" else "internal server error"
    return JSONResponse(
        status_code=500,
        content=fail("internal server error", code=500, data={"detail": detail}),
    )
