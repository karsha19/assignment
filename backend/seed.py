import uuid
from datetime import datetime, timedelta

from app.db.session import SessionLocal, engine, Base
from app.models import models as m
from app.core.security import hash_password
from app.services.matching import normalize_identifier

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def get_or_create_user(username, password, role):
    user = db.query(m.User).filter(m.User.username == username).first()
    if user:
        return user
    user = m.User(username=username, hashed_password=hash_password(password), role=role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_camera(code, **kwargs):
    cam = db.query(m.Camera).filter(m.Camera.camera_code == code).first()
    if cam:
        stream_reference = kwargs.get("stream_reference")
        if stream_reference and cam.stream_reference != stream_reference:
            cam.stream_reference = stream_reference
        if "is_enabled" in kwargs:
            cam.is_enabled = bool(kwargs["is_enabled"])
        if "status" in kwargs:
            cam.status = kwargs["status"]
        if "last_heartbeat" in kwargs:
            cam.last_heartbeat = kwargs["last_heartbeat"]
        db.commit()
        db.refresh(cam)
        return cam
    cam = m.Camera(camera_code=code, **kwargs)
    db.add(cam)
    db.commit()
    db.refresh(cam)
    return cam


def main():
    admin = get_or_create_user("admin", "Admin@12345", m.RoleEnum.admin)
    operator = get_or_create_user("operator", "Operator@12345", m.RoleEnum.operator)

    cam1 = get_or_create_camera(
        "C001",
        name="Ahmedabad Traffic Junction",
        department="Traffic Police",
        zone="Zone-1",
        latitude=23.0225,
        longitude=72.5714,
        camera_type="fixed_junction",
        source_protocol=m.SourceProtocolEnum.simulated,
        stream_reference="/media/sample/VIRAT_S_010204_05_000856_000890.mp4",
        status=m.CameraStatusEnum.online,
        is_enabled=True,
        last_heartbeat=datetime.utcnow(),
        storage_metadata={"retention_days": 30},
    )
    cam2 = get_or_create_camera(
        "C002",
        name="RTO Checkpoint",
        department="RTO",
        zone="Zone-2",
        latitude=23.0395,
        longitude=72.5660,
        camera_type="checkpoint",
        source_protocol=m.SourceProtocolEnum.simulated,
        stream_reference="/media/sample/VIRAT_S_050201_05_000890_000944.mp4",
        status=m.CameraStatusEnum.online,
        is_enabled=True,
        last_heartbeat=datetime.utcnow(),
        storage_metadata={"retention_days": 30},
    )

    watchlisted_plate = "GJ01XX0001"
    normal_plate = "GJ05YY4321"

    existing_wl = db.query(m.WatchlistRecord).filter(
        m.WatchlistRecord.normalized_identifier == normalize_identifier(watchlisted_plate)
    ).first()
    if not existing_wl:
        wl = m.WatchlistRecord(
            entity_type=m.WatchlistEntityTypeEnum.stolen_vehicle,
            identifier=watchlisted_plate,
            normalized_identifier=normalize_identifier(watchlisted_plate),
            display_name="Stolen vehicle - synthetic demo record",
            reason="Reported stolen (synthetic demo data)",
            description="Demonstration-only synthetic watchlist record. Not a real case.",
            status=m.WatchlistStatusEnum.active,
        )
        db.add(wl)
        db.commit()
        db.refresh(wl)
    else:
        wl = existing_wl

    base_time = datetime.utcnow() - timedelta(hours=2)

    def add_event(camera, identifier, minutes_offset, confidence, event_type=m.EventTypeEnum.anpr):
        key = f"seed-{camera.camera_code}-{identifier}-{minutes_offset}"
        existing = db.query(m.AnalyticsEvent).filter(m.AnalyticsEvent.idempotency_key == key).first()
        if existing:
            return existing
        ev = m.AnalyticsEvent(
            idempotency_key=key,
            camera_id=camera.id,
            event_type=event_type,
            entity_identifier=identifier,
            normalized_identifier=normalize_identifier(identifier),
            confidence=confidence,
            vehicle_type="sedan",
            event_timestamp=base_time + timedelta(minutes=minutes_offset),
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev

    ev1 = add_event(cam1, watchlisted_plate, 2, 0.94)
    ev2 = add_event(cam2, watchlisted_plate, 18, 0.91)
    ev3 = add_event(cam1, watchlisted_plate, 41, 0.88)

    add_event(cam2, normal_plate, 25, 0.90)

    def ensure_alert(event, status, ack=False, resolve=False):
        existing = db.query(m.Alert).filter(m.Alert.analytics_event_id == event.id).first()
        if existing:
            return existing
        alert = m.Alert(
            alert_type="watchlist_match",
            severity=m.AlertSeverityEnum.critical,
            status=status,
            watchlist_record_id=wl.id,
            analytics_event_id=event.id,
            camera_id=event.camera_id,
            matched_identifier=event.entity_identifier,
            confidence=event.confidence,
            detection_timestamp=event.event_timestamp,
        )
        if ack or resolve:
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = operator.id
            alert.status = m.AlertStatusEnum.acknowledged
        if resolve:
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = operator.id
            alert.status = m.AlertStatusEnum.resolved
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    ensure_alert(ev1, m.AlertStatusEnum.resolved, resolve=True)
    ensure_alert(ev2, m.AlertStatusEnum.acknowledged, ack=True)
    ensure_alert(ev3, m.AlertStatusEnum.new)

    print("Seed complete.")
    print("Admin login: admin / Admin@12345")
    print("Operator login: operator / Operator@12345")
    print(f"Watchlisted plate for demo: {watchlisted_plate}")


if __name__ == "__main__":
    main()
