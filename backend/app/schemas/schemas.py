from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class CameraBase(BaseModel):
    camera_code: str = Field(..., min_length=1, max_length=32)
    name: str = Field(..., min_length=1, max_length=128)
    department: Optional[str] = None
    zone: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    camera_type: Optional[str] = None
    source_protocol: str = "recorded"
    stream_reference: Optional[str] = None
    storage_metadata: Optional[Dict[str, Any]] = None

    @field_validator("source_protocol")
    @classmethod
    def validate_protocol(cls, v):
        allowed = {"recorded", "simulated", "rtsp", "onvif", "vendor_api"}
        if v not in allowed:
            raise ValueError(f"source_protocol must be one of {allowed}")
        return v


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    zone: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    camera_type: Optional[str] = None
    source_protocol: Optional[str] = None
    stream_reference: Optional[str] = None
    storage_metadata: Optional[Dict[str, Any]] = None


class CameraOut(BaseModel):
    id: str
    camera_code: str
    name: str
    department: Optional[str]
    zone: Optional[str]
    latitude: float
    longitude: float
    camera_type: Optional[str]
    source_protocol: str
    status: str
    last_heartbeat: Optional[datetime]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    playback_url: Optional[str] = None

    class Config:
        from_attributes = True


class AnalyticsEventCreate(BaseModel):
    idempotency_key: str = Field(..., min_length=1, max_length=128)
    camera_id: str
    event_type: str
    entity_identifier: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)
    vehicle_type: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    event_timestamp: datetime

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        allowed = {"anpr", "vehicle_detection", "person_detection", "object_detection"}
        if v not in allowed:
            raise ValueError(f"event_type must be one of {allowed}")
        return v


class AnalyticsEventOut(BaseModel):
    id: str
    camera_id: str
    event_type: str
    entity_identifier: Optional[str]
    confidence: float
    vehicle_type: Optional[str]
    event_timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class WatchlistCreate(BaseModel):
    entity_type: str
    identifier: str = Field(..., min_length=1, max_length=64)
    display_name: Optional[str] = None
    reason: Optional[str] = None
    description: Optional[str] = None
    expiry_at: Optional[datetime] = None

    @field_validator("entity_type")
    @classmethod
    def validate_entity_type(cls, v):
        allowed = {"stolen_vehicle", "blacklisted_vehicle", "wanted_person", "missing_person", "other"}
        if v not in allowed:
            raise ValueError(f"entity_type must be one of {allowed}")
        return v


class WatchlistUpdate(BaseModel):
    display_name: Optional[str] = None
    reason: Optional[str] = None
    description: Optional[str] = None
    expiry_at: Optional[datetime] = None


class WatchlistOut(BaseModel):
    id: str
    entity_type: str
    identifier: str
    display_name: Optional[str]
    reason: Optional[str]
    status: str
    description: Optional[str]
    expiry_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: str
    alert_type: str
    severity: str
    status: str
    camera_id: str
    matched_identifier: str
    confidence: float
    detection_timestamp: datetime
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


class MovementEvent(BaseModel):
    camera_id: str
    camera_name: str
    latitude: float
    longitude: float
    timestamp: datetime
    confidence: float
    event_type: str


class MovementHistoryOut(BaseModel):
    identifier: str
    normalized_identifier: str
    events: List[MovementEvent]


class AuditLogOut(BaseModel):
    id: str
    actor_user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    result: str
    created_at: datetime

    class Config:
        from_attributes = True
