import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1 import auth, cameras, watchlist, analytics, alerts, entities, audit, ws
from app.services.heartbeat import run_heartbeat_monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_heartbeat_monitor())
    yield
    task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cameras.router)
app.include_router(watchlist.router)
app.include_router(analytics.router)
app.include_router(alerts.router)
app.include_router(entities.router)
app.include_router(audit.router)
app.include_router(ws.router)

# Serves recorded/simulated sample footage only (see data/sample/README.md).
# This is NOT a live streaming endpoint; it is a plain static file server
# used to demonstrate the recorded-video playback workflow.
_MEDIA_DIR = "/media/sample"
if os.path.isdir(_MEDIA_DIR):
    app.mount("/media/sample", StaticFiles(directory=_MEDIA_DIR), name="sample-media")


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}
