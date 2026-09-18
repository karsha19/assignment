from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import AnalyticsEvent, Camera, User
from app.schemas.schemas import MovementHistoryOut, MovementEvent
from app.core.security import get_current_user
from app.services.matching import normalize_identifier

router = APIRouter(prefix="/api/v1/entities", tags=["entities"])


@router.get("/{identifier}/movement-history", response_model=MovementHistoryOut)
def movement_history(identifier: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    normalized = normalize_identifier(identifier)
    if not normalized:
        raise HTTPException(status_code=422, detail="Invalid identifier")

    events = (
        db.query(AnalyticsEvent)
        .filter(AnalyticsEvent.normalized_identifier == normalized)
        .order_by(AnalyticsEvent.event_timestamp.asc())
        .all()
    )

    movement_events = []
    for e in events:
        camera = db.query(Camera).filter(Camera.id == e.camera_id).first()
        if not camera or camera.latitude is None or camera.longitude is None:
            continue
        movement_events.append(
            MovementEvent(
                camera_id=camera.id,
                camera_name=camera.name,
                latitude=camera.latitude,
                longitude=camera.longitude,
                timestamp=e.event_timestamp,
                confidence=e.confidence,
                event_type=e.event_type.value,
            )
        )

    return MovementHistoryOut(identifier=identifier, normalized_identifier=normalized, events=movement_events)
