from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from backend.auth import router as auth_router
from backend.clockify import router as clockify_router
from backend.database import DATABASE_URL, init_db
from backend.private import router as private_router
from backend.public import router as public_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
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

# Mount frontend last to avoid overshadowing /api routes
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):  # pragma: no cover
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return Response(status_code=404)
