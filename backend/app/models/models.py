import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey,
    Enum, UniqueConstraint, Index, JSON
)
from sqlalchemy.orm import relationship

from app.db.session import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class RoleEnum(str, enum.Enum):
    admin = "admin"
    operator = "operator"


class CameraStatusEnum(str, enum.Enum):
    online = "online"
    offline = "offline"
    degraded = "degraded"


class SourceProtocolEnum(str, enum.Enum):
    recorded = "recorded"
    simulated = "simulated"
    rtsp = "rtsp"
    onvif = "onvif"
    vendor_api = "vendor_api"


class EventTypeEnum(str, enum.Enum):
    anpr = "anpr"
    vehicle_detection = "vehicle_detection"
    person_detection = "person_detection"
    object_detection = "object_detection"


class WatchlistEntityTypeEnum(str, enum.Enum):
    stolen_vehicle = "stolen_vehicle"
    blacklisted_vehicle = "blacklisted_vehicle"
    wanted_person = "wanted_person"
    missing_person = "missing_person"
    other = "other"


class WatchlistStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class AlertSeverityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AlertStatusEnum(str, enum.Enum):
    new = "new"
    acknowledged = "acknowledged"
    resolved = "resolved"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    username = Column(String(64), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.operator)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    camera_code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    department = Column(String(64), nullable=True, index=True)
    zone = Column(String(64), nullable=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    camera_type = Column(String(64), nullable=True)
    source_protocol = Column(Enum(SourceProtocolEnum), nullable=False, default=SourceProtocolEnum.recorded)
    stream_reference = Column(String(512), nullable=True)
    status = Column(Enum(CameraStatusEnum), nullable=False, default=CameraStatusEnum.offline, index=True)
    last_heartbeat = Column(DateTime, nullable=True)
    storage_metadata = Column(JSON, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    health_events = relationship("CameraHealthEvent", back_populates="camera", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_camera_dept_zone", "department", "zone"),
    )


class CameraHealthEvent(Base):
    __tablename__ = "camera_health_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    camera_id = Column(String(36), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(CameraStatusEnum), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    camera = relationship("Camera", back_populates="health_events")


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    camera_id = Column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)
    event_type = Column(Enum(EventTypeEnum), nullable=False)
    entity_identifier = Column(String(64), nullable=True, index=True)
    normalized_identifier = Column(String(64), nullable=True, index=True)
    confidence = Column(Float, nullable=False)
    vehicle_type = Column(String(64), nullable=True)
    bounding_box = Column(JSON, nullable=True)
    raw_metadata = Column(JSON, nullable=True)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    camera = relationship("Camera")


class WatchlistRecord(Base):
    __tablename__ = "watchlist_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    entity_type = Column(Enum(WatchlistEntityTypeEnum), nullable=False)
    identifier = Column(String(64), nullable=False, index=True)
    normalized_identifier = Column(String(64), nullable=False, index=True)
    display_name = Column(String(128), nullable=True)
    reason = Column(String(256), nullable=True)
    status = Column(Enum(WatchlistStatusEnum), nullable=False, default=WatchlistStatusEnum.active, index=True)
    description = Column(Text, nullable=True)
    expiry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("normalized_identifier", "entity_type", name="uq_watchlist_identifier_type"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    alert_type = Column(String(64), nullable=False, default="watchlist_match")
    severity = Column(Enum(AlertSeverityEnum), nullable=False, default=AlertSeverityEnum.high)
    status = Column(Enum(AlertStatusEnum), nullable=False, default=AlertStatusEnum.new, index=True)
    watchlist_record_id = Column(String(36), ForeignKey("watchlist_records.id"), nullable=False)
    analytics_event_id = Column(String(36), ForeignKey("analytics_events.id"), nullable=False, unique=True)
    camera_id = Column(String(36), ForeignKey("cameras.id"), nullable=False, index=True)
    matched_identifier = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    detection_timestamp = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    watchlist_record = relationship("WatchlistRecord")
    analytics_event = relationship("AnalyticsEvent")
    camera = relationship("Camera")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    result = Column(String(32), nullable=False, default="success")
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
