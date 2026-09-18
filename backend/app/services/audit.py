from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import AuditLog


def record_audit(
    db: Session,
    actor_user_id: Optional[str],
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    result: str = "success",
    metadata: Optional[Dict[str, Any]] = None,
):
    entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.commit()
