from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.models.models import (
    AnalyticsEvent, Camera, WatchlistRecord, WatchlistStatusEnum,
    Alert, AlertSeverityEnum, AlertStatusEnum, User,
)
from app.schemas.schemas import AnalyticsEventCreate, AnalyticsEventOut, AlertOut
from app.core.security import get_current_user
from app.services.matching import normalize_identifier
from app.services.audit import record_audit
from app.websocket.manager import manager

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.post("/events", response_model=AnalyticsEventOut, status_code=201)
async def ingest_event(
    payload: AnalyticsEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    camera = db.query(Camera).filter(Camera.id == payload.camera_id).first()
    if not camera:
        raise HTTPException(status_code=422, detail="Unknown camera_id")
    if not camera.is_enabled:
        raise HTTPException(status_code=422, detail="Camera is disabled and cannot report events")

    if payload.event_type == "anpr" and not payload.entity_identifier:
        raise HTTPException(status_code=422, detail="entity_identifier is required for anpr events")

    existing = db.query(AnalyticsEvent).filter(AnalyticsEvent.idempotency_key == payload.idempotency_key).first()
    if existing:
        raise HTTPException(status_code=409, detail="Duplicate event: idempotency_key already processed")

    normalized = normalize_identifier(payload.entity_identifier) if payload.entity_identifier else None

    event = AnalyticsEvent(
        idempotency_key=payload.idempotency_key,
        camera_id=payload.camera_id,
        event_type=payload.event_type,
        entity_identifier=payload.entity_identifier,
        normalized_identifier=normalized,
        confidence=payload.confidence,
        vehicle_type=payload.vehicle_type,
        bounding_box=payload.bounding_box,
        raw_metadata=payload.raw_metadata,
        event_timestamp=payload.event_timestamp,
    )

    try:
        db.add(event)
        db.commit()
        db.refresh(event)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate event: idempotency_key already processed")

    await manager.broadcast(
        "analytics_event",
        {
            "event_id": event.id,
            "camera_id": event.camera_id,
            "event_type": event.event_type.value,
            "entity_identifier": event.entity_identifier,
            "confidence": event.confidence,
            "timestamp": event.event_timestamp,
        },
    )

    alert = None
    if normalized:
        match = (
            db.query(WatchlistRecord)
            .filter(
                WatchlistRecord.normalized_identifier == normalized,
                WatchlistRecord.status == WatchlistStatusEnum.active,
            )
            .first()
        )
        if match and (match.expiry_at is None or match.expiry_at > datetime.utcnow()):
            severity = AlertSeverityEnum.critical if match.entity_type.value in (
                "stolen_vehicle", "wanted_person"
            ) else AlertSeverityEnum.high

            alert = Alert(
                alert_type="watchlist_match",
                severity=severity,
                status=AlertStatusEnum.new,
                watchlist_record_id=match.id,
                analytics_event_id=event.id,
                camera_id=camera.id,
                matched_identifier=payload.entity_identifier,
                confidence=payload.confidence,
                detection_timestamp=payload.event_timestamp,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)

            record_audit(db, current_user.id, "alert_generated", "alert", alert.id, metadata={
                "watchlist_record_id": match.id, "analytics_event_id": event.id,
            })

            await manager.broadcast(
                "watchlist_match",
                {
                    "alert_id": alert.id,
                    "camera_id": camera.id,
                    "camera_name": camera.name,
                    "matched_identifier": alert.matched_identifier,
                    "entity_type": match.entity_type.value,
                    "reason": match.reason,
                    "severity": alert.severity.value,
                    "confidence": alert.confidence,
                    "detection_timestamp": alert.detection_timestamp,
                },
            )
            await manager.broadcast(
                "new_alert",
                {
                    "alert_id": alert.id,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "camera_id": camera.id,
                    "matched_identifier": alert.matched_identifier,
                    "created_at": alert.created_at,
                },
            )

    return event


@router.get("/events", response_model=List[AnalyticsEventOut])
def list_events(
    camera_id: Optional[str] = None,
    event_type: Optional[str] = None,
    entity_identifier: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(AnalyticsEvent)
    if camera_id:
        query = query.filter(AnalyticsEvent.camera_id == camera_id)
    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)
    if entity_identifier:
        query = query.filter(AnalyticsEvent.normalized_identifier == normalize_identifier(entity_identifier))
    if start:
        query = query.filter(AnalyticsEvent.event_timestamp >= start)
    if end:
        query = query.filter(AnalyticsEvent.event_timestamp <= end)
    return query.order_by(AnalyticsEvent.event_timestamp.desc()).offset(offset).limit(limit).all()


@router.get("/events/{event_id}", response_model=AnalyticsEventOut)
def get_event(event_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(AnalyticsEvent).filter(AnalyticsEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
