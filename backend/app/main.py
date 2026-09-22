import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.v1 import auth, cameras, watchlist, analytics, alerts, entities, audit, ws
from app.services.heartbeat import run_heartbeat_monitor
from app.db.session import SessionLocal
from app.models.models import User

# seed.py lives at the backend package root and provides an idempotent
# data seeder used for demo deployments.
try:
    import seed as seeder
except Exception:
    seeder = None

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # If the database has no users, optionally populate demo data so
    # deployments (eg. Render) get a working admin/operator account.
    # To avoid seeding in production, this runs only when
    # `settings.ENV != "production"` or when `SEED_ON_STARTUP=1` is set.
    db = SessionLocal()
    try:
        try:
            user_count = db.query(User).count()
        except Exception:
            user_count = 0
        if seeder is not None and (settings.ENV != "production" or os.getenv("SEED_ON_STARTUP", "") == "1"):
            if user_count == 0:
                logger.info("No users found in DB; running demo seeder to create admin/operator accounts")
                try:
                    seeder.main()
                except Exception:
                    logger.exception("Seeder run failed")
            else:
                from app.models.models import Camera, CameraStatusEnum
                for cam in db.query(Camera).all():
                    if cam.camera_code in {"C001", "C002"} and not cam.is_enabled:
                        cam.is_enabled = True
                        cam.status = CameraStatusEnum.online
                db.commit()
    finally:
        db.close()

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
# used to demonstrate the recorded-video playback workflow. See
# Settings.resolved_media_dir for how this path is chosen (Docker vs.
# running from source).
_MEDIA_DIR = settings.resolved_media_dir
if os.path.isdir(_MEDIA_DIR):
    app.mount("/media/sample", StaticFiles(directory=_MEDIA_DIR), name="sample-media")
    logger.info("Serving sample videos from %s at /media/sample", _MEDIA_DIR)
else:
    logger.warning(
        "Sample video directory not found at %s -- camera video playback will "
        "show 'Playback failed'. Set MEDIA_DIR or check data/sample/ exists.",
        _MEDIA_DIR,
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}
