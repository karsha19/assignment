from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "operator", name="roleenum"), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])

    op.create_table(
        "cameras",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("camera_code", sa.String(32), nullable=False, unique=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("department", sa.String(64), nullable=True),
        sa.Column("zone", sa.String(64), nullable=True),
        sa.Column("latitude", sa.Float, nullable=False),
        sa.Column("longitude", sa.Float, nullable=False),
        sa.Column("camera_type", sa.String(64), nullable=True),
        sa.Column("source_protocol", sa.Enum("recorded", "simulated", "rtsp", "onvif", "vendor_api", name="sourceprotocolenum"), nullable=False),
        sa.Column("stream_reference", sa.String(512), nullable=True),
        sa.Column("status", sa.Enum("online", "offline", "degraded", name="camerastatusenum"), nullable=False),
        sa.Column("last_heartbeat", sa.DateTime, nullable=True),
        sa.Column("storage_metadata", sa.JSON, nullable=True),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_cameras_camera_code", "cameras", ["camera_code"])
    op.create_index("ix_cameras_department", "cameras", ["department"])
    op.create_index("ix_cameras_zone", "cameras", ["zone"])
    op.create_index("ix_cameras_status", "cameras", ["status"])
    op.create_index("ix_cameras_is_enabled", "cameras", ["is_enabled"])
    op.create_index("ix_camera_dept_zone", "cameras", ["department", "zone"])

    op.create_table(
        "camera_health_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("camera_id", sa.String(36), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Enum("online", "offline", "degraded", name="camerastatusenum2", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_camera_health_events_camera_id", "camera_health_events", ["camera_id"])
    op.create_index("ix_camera_health_events_created_at", "camera_health_events", ["created_at"])

    op.create_table(
        "watchlist_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_type", sa.Enum("stolen_vehicle", "blacklisted_vehicle", "wanted_person", "missing_person", "other", name="watchlistentitytypeenum"), nullable=False),
        sa.Column("identifier", sa.String(64), nullable=False),
        sa.Column("normalized_identifier", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("reason", sa.String(256), nullable=True),
        sa.Column("status", sa.Enum("active", "inactive", name="watchliststatusenum"), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("expiry_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("normalized_identifier", "entity_type", name="uq_watchlist_identifier_type"),
    )
    op.create_index("ix_watchlist_records_identifier", "watchlist_records", ["identifier"])
    op.create_index("ix_watchlist_records_normalized_identifier", "watchlist_records", ["normalized_identifier"])
    op.create_index("ix_watchlist_records_status", "watchlist_records", ["status"])

    op.create_table(
        "analytics_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False, unique=True),
        sa.Column("camera_id", sa.String(36), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("event_type", sa.Enum("anpr", "vehicle_detection", "person_detection", "object_detection", name="eventtypeenum"), nullable=False),
        sa.Column("entity_identifier", sa.String(64), nullable=True),
        sa.Column("normalized_identifier", sa.String(64), nullable=True),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("vehicle_type", sa.String(64), nullable=True),
        sa.Column("bounding_box", sa.JSON, nullable=True),
        sa.Column("raw_metadata", sa.JSON, nullable=True),
        sa.Column("event_timestamp", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_analytics_events_idempotency_key", "analytics_events", ["idempotency_key"])
    op.create_index("ix_analytics_events_camera_id", "analytics_events", ["camera_id"])
    op.create_index("ix_analytics_events_entity_identifier", "analytics_events", ["entity_identifier"])
    op.create_index("ix_analytics_events_normalized_identifier", "analytics_events", ["normalized_identifier"])
    op.create_index("ix_analytics_events_event_timestamp", "analytics_events", ["event_timestamp"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_type", sa.String(64), nullable=False),
        sa.Column("severity", sa.Enum("low", "medium", "high", "critical", name="alertseverityenum"), nullable=False),
        sa.Column("status", sa.Enum("new", "acknowledged", "resolved", name="alertstatusenum"), nullable=False),
        sa.Column("watchlist_record_id", sa.String(36), sa.ForeignKey("watchlist_records.id"), nullable=False),
        sa.Column("analytics_event_id", sa.String(36), sa.ForeignKey("analytics_events.id"), nullable=False, unique=True),
        sa.Column("camera_id", sa.String(36), sa.ForeignKey("cameras.id"), nullable=False),
        sa.Column("matched_identifier", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("detection_timestamp", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("acknowledged_at", sa.DateTime, nullable=True),
        sa.Column("acknowledged_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_camera_id", "alerts", ["camera_id"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("actor_user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(64), nullable=True),
        sa.Column("result", sa.String(32), nullable=False),
        sa.Column("metadata_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_audit_logs_actor_user_id", "audit_logs", ["actor_user_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    op.drop_table("audit_logs")
    op.drop_table("alerts")
    op.drop_table("analytics_events")
    op.drop_table("watchlist_records")
    op.drop_table("camera_health_events")
    op.drop_table("cameras")
    op.drop_table("users")
