from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.session import get_db
from app.models.models import Camera, CameraHealthEvent, CameraStatusEnum, User, AnalyticsEvent
from app.schemas.schemas import CameraCreate, CameraUpdate, CameraOut, AnalyticsEventOut
from app.core.security import get_current_user, require_role
from app.core.config import settings
from app.adapters.camera_adapters import get_adapter
from app.services.audit import record_audit
from app.websocket.manager import manager

router = APIRouter(prefix="/api/v1/cameras", tags=["cameras"])


def _to_out(camera: Camera) -> CameraOut:
    adapter = get_adapter(camera.source_protocol.value, camera.camera_code, camera.stream_reference)
    playback_url = None
    try:
        info = adapter.get_stream_info()
        playback_url = info.playback_reference
    except NotImplementedError:
        playback_url = None
    out = CameraOut.model_validate(camera)
    out.playback_url = playback_url
    return out


@router.get("", response_model=List[CameraOut])
def list_cameras(
    q: Optional[str] = None,
    department: Optional[str] = None,
    zone: Optional[str] = None,
    camera_type: Optional[str] = None,
    source_protocol: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    is_enabled: Optional[bool] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Camera)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Camera.camera_code.like(like), Camera.name.like(like)))
    if department:
        query = query.filter(Camera.department == department)
    if zone:
        query = query.filter(Camera.zone == zone)
    if camera_type:
        query = query.filter(Camera.camera_type == camera_type)
    if source_protocol:
        query = query.filter(Camera.source_protocol == source_protocol)
    if status_filter:
        query = query.filter(Camera.status == status_filter)
    if is_enabled is not None:
        query = query.filter(Camera.is_enabled == is_enabled)

    cameras = query.order_by(Camera.created_at.desc()).offset(offset).limit(limit).all()
    return [_to_out(c) for c in cameras]


@router.post("", response_model=CameraOut, status_code=201)
async def create_camera(
    payload: CameraCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    existing = db.query(Camera).filter(Camera.camera_code == payload.camera_code).first()
    if existing:
        raise HTTPException(status_code=409, detail="camera_code already exists")

    camera = Camera(**payload.model_dump())
    camera.status = CameraStatusEnum.offline
    db.add(camera)
    db.commit()
    db.refresh(camera)

    record_audit(db, current_user.id, "camera_created", "camera", camera.id, metadata={"camera_code": camera.camera_code})
    await manager.broadcast("camera_created", {"camera_id": camera.id, "camera_code": camera.camera_code})
    return _to_out(camera)


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return _to_out(camera)


@router.patch("/{camera_id}", response_model=CameraOut)
async def update_camera(
    camera_id: str,
    payload: CameraUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(camera, field, value)
    db.commit()
    db.refresh(camera)

    record_audit(db, current_user.id, "camera_updated", "camera", camera.id, metadata={"changed_fields": list(changes.keys())})
    await manager.broadcast("camera_updated", {"camera_id": camera.id})
    return _to_out(camera)


@router.post("/{camera_id}/enable", response_model=CameraOut)
async def enable_camera(camera_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    camera.is_enabled = True
    db.commit()
    db.refresh(camera)
    record_audit(db, current_user.id, "camera_enabled", "camera", camera.id)
    await manager.broadcast("camera_updated", {"camera_id": camera.id})
    return _to_out(camera)


@router.post("/{camera_id}/disable", response_model=CameraOut)
async def disable_camera(camera_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    camera.is_enabled = False
    camera.status = CameraStatusEnum.offline
    db.commit()
    db.refresh(camera)
    record_audit(db, current_user.id, "camera_disabled", "camera", camera.id)
    await manager.broadcast("camera_updated", {"camera_id": camera.id})
    return _to_out(camera)


@router.get("/{camera_id}/health")
def camera_health(camera_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    recent = (
        db.query(CameraHealthEvent)
        .filter(CameraHealthEvent.camera_id == camera_id)
        .order_by(CameraHealthEvent.created_at.desc())
        .limit(20)
        .all()
    )
    return {
        "camera_id": camera_id,
        "current_status": camera.status.value,
        "last_heartbeat": camera.last_heartbeat,
        "history": [{"status": h.status.value, "at": h.created_at} for h in recent],
    }


@router.get("/{camera_id}/events", response_model=List[AnalyticsEventOut])
def camera_events(camera_id: str, limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    events = (
        db.query(AnalyticsEvent)
        .filter(AnalyticsEvent.camera_id == camera_id)
        .order_by(AnalyticsEvent.event_timestamp.desc())
        .limit(limit)
        .all()
    )
    return events


@router.post("/{camera_id}/heartbeat")
async def submit_heartbeat(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera or not camera.is_enabled:
        raise HTTPException(status_code=404, detail="Camera not found or disabled")

    camera.last_heartbeat = datetime.utcnow()
    if camera.status != CameraStatusEnum.online:
        camera.status = CameraStatusEnum.online
        db.add(CameraHealthEvent(camera_id=camera.id, status=CameraStatusEnum.online))
        await manager.broadcast("camera_health_changed", {"camera_id": camera.id, "status": "online"})
    db.commit()
    return {"camera_id": camera.id, "status": camera.status.value, "last_heartbeat": camera.last_heartbeat}
