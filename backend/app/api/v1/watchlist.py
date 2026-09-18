from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import WatchlistRecord, WatchlistStatusEnum, User
from app.schemas.schemas import WatchlistCreate, WatchlistUpdate, WatchlistOut
from app.core.security import get_current_user, require_role
from app.services.matching import normalize_identifier
from app.services.audit import record_audit

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


@router.get("", response_model=List[WatchlistOut])
def list_watchlist(
    q: Optional[str] = None,
    entity_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(WatchlistRecord)
    if q:
        query = query.filter(WatchlistRecord.identifier.like(f"%{q}%"))
    if entity_type:
        query = query.filter(WatchlistRecord.entity_type == entity_type)
    if status_filter:
        query = query.filter(WatchlistRecord.status == status_filter)
    return query.order_by(WatchlistRecord.created_at.desc()).offset(offset).limit(limit).all()


@router.post("", response_model=WatchlistOut, status_code=201)
def create_watchlist_record(
    payload: WatchlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    normalized = normalize_identifier(payload.identifier)
    existing = (
        db.query(WatchlistRecord)
        .filter(WatchlistRecord.normalized_identifier == normalized, WatchlistRecord.entity_type == payload.entity_type)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="A watchlist record with this identifier and entity type already exists")

    record = WatchlistRecord(
        entity_type=payload.entity_type,
        identifier=payload.identifier,
        normalized_identifier=normalized,
        display_name=payload.display_name,
        reason=payload.reason,
        description=payload.description,
        expiry_at=payload.expiry_at,
        status=WatchlistStatusEnum.active,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    record_audit(db, current_user.id, "watchlist_created", "watchlist_record", record.id)
    return record


@router.get("/{record_id}", response_model=WatchlistOut)
def get_watchlist_record(record_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    record = db.query(WatchlistRecord).filter(WatchlistRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    return record


@router.patch("/{record_id}", response_model=WatchlistOut)
def update_watchlist_record(
    record_id: str,
    payload: WatchlistUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    record = db.query(WatchlistRecord).filter(WatchlistRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    record_audit(db, current_user.id, "watchlist_updated", "watchlist_record", record.id, metadata={"changed_fields": list(changes.keys())})
    return record


@router.post("/{record_id}/enable", response_model=WatchlistOut)
def enable_watchlist_record(record_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    record = db.query(WatchlistRecord).filter(WatchlistRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    record.status = WatchlistStatusEnum.active
    db.commit()
    record_audit(db, current_user.id, "watchlist_enabled", "watchlist_record", record.id)
    return record


@router.post("/{record_id}/disable", response_model=WatchlistOut)
def disable_watchlist_record(record_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin"))):
    record = db.query(WatchlistRecord).filter(WatchlistRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    record.status = WatchlistStatusEnum.inactive
    db.commit()
    record_audit(db, current_user.id, "watchlist_disabled", "watchlist_record", record.id)
    return record
