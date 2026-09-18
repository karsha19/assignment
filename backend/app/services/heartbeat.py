"""
Documented simulated heartbeat thresholding.

Real cameras/edge-gateways would push heartbeats to POST
/api/v1/cameras/{camera_id}/heartbeat on a fixed interval (e.g. every 15s).
This background task periodically demotes cameras whose last_heartbeat is
older than the configured thresholds to 'degraded' or 'offline', and
broadcasts the change over WebSocket so dashboards update without a refresh.

To replace the simulator with a real heartbeat service: point the actual
camera/edge-gateway health probe at the heartbeat endpoint (with a
service-to-service credential) instead of relying on this thresholding pass
to only ever move cameras toward 'offline'.
"""
import asyncio
from datetime import datetime, timedelta

from app.db.session import SessionLocal
from app.models.models import Camera, CameraHealthEvent, CameraStatusEnum
from app.core.config import settings
from app.websocket.manager import manager


async def run_heartbeat_monitor(interval_seconds: int = 15):
    while True:
        await _evaluate_once()
        await asyncio.sleep(interval_seconds)


async def _evaluate_once():
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        cameras = db.query(Camera).filter(Camera.is_enabled == True).all()  # noqa: E712
        for camera in cameras:
            if camera.last_heartbeat is None:
                continue
            age = (now - camera.last_heartbeat).total_seconds()
            new_status = camera.status
            if age > settings.HEARTBEAT_OFFLINE_SECONDS:
                new_status = CameraStatusEnum.offline
            elif age > settings.HEARTBEAT_DEGRADED_SECONDS:
                new_status = CameraStatusEnum.degraded

            if new_status != camera.status:
                camera.status = new_status
                db.add(CameraHealthEvent(camera_id=camera.id, status=new_status))
                db.commit()
                await manager.broadcast(
                    "camera_health_changed",
                    {"camera_id": camera.id, "status": new_status.value},
                )
    finally:
        db.close()
