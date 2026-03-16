from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.responses import Response

from backend.auth import router as auth_router
from backend.clockify import router as clockify_router
from backend.database import DATABASE_URL, init_db
from backend.logging_config import APP_LOG_FILE, configure_application_logging
from backend.private import router as private_router
from backend.public import router as public_router


configure_application_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    logger.info("Application startup complete. Log file: %s", APP_LOG_FILE)
    yield


app = FastAPI(title="Time Audit API", lifespan=lifespan)

# CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(public_router)
app.include_router(clockify_router)
app.include_router(private_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "database_url": DATABASE_URL}

# Serve the built SPA for non-API routes, including direct deep links like /login.
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
FRONTEND_INDEX = os.path.join(FRONTEND_DIST, "index.html")


def _resolve_frontend_path(path: str) -> str | None:
    if not path:
        return None

    normalized_path = os.path.abspath(os.path.join(FRONTEND_DIST, path))
    if normalized_path == FRONTEND_DIST or normalized_path.startswith(f"{FRONTEND_DIST}{os.sep}"):
        return normalized_path
    return None


if os.path.isdir(FRONTEND_DIST):
    @app.get("/", include_in_schema=False)
    async def frontend_index():  # pragma: no cover
        if os.path.exists(FRONTEND_INDEX):
            return FileResponse(FRONTEND_INDEX)
        return Response(status_code=404)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):  # pragma: no cover
        if full_path.startswith("api/"):
            return Response(status_code=404)

        requested_path = _resolve_frontend_path(full_path)
        if requested_path and os.path.isfile(requested_path):
            return FileResponse(requested_path)

        if os.path.exists(FRONTEND_INDEX):
            return FileResponse(FRONTEND_INDEX)
        return Response(status_code=404)
