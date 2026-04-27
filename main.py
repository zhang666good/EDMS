from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

try:
    from dotenv import load_dotenv
except ImportError:  # Keep app runnable even if dependency is missing in dev env.
    def load_dotenv(*args, **kwargs):
        return False

# Load project .env once at startup; existing system env vars keep higher priority.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=False)

from app.api.gateway import router as gateway_router
from app.api.openai_compat import router as openai_compat_router
from app.api.file_upload_and_context import router as file_upload_router
from app.api.knowledge import router as knowledge_router
from app.api.backend import router as backend_router

app = FastAPI(title="Enterprise Decision Making System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(gateway_router)
app.include_router(openai_compat_router)
app.include_router(file_upload_router)
app.include_router(knowledge_router)
app.include_router(backend_router)

# 挂载静态文件目录（知识库管理页面）
web_dir = Path(__file__).resolve().parent / "app" / "web"
if web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")


def _request_id(request: Request):
    return request.headers.get("X-Request-Id")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "detail": exc.errors(),
            "request_id": _request_id(request),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        detail = dict(exc.detail)
        detail.setdefault("request_id", _request_id(request))
        return JSONResponse(status_code=exc.status_code, content=detail)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": "HTTP_ERROR",
            "message": str(exc.detail),
            "detail": None,
            "request_id": _request_id(request),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Unhandled server error",
            "detail": str(exc),
            "request_id": _request_id(request),
        },
    )


@app.get("/")
async def root():
    return {"message": "Enterprise decision gateway is running"}


@app.get("/admin")
async def admin_page():
    """知识库管理页面"""
    web_dir = Path(__file__).resolve().parent / "app" / "web"
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse(status_code=404, content={"message": "Page not found"})
