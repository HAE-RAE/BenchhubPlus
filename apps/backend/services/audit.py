"""Audit logging service."""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from sqlalchemy.orm import Session

from ...core.db import AuditLog


class AuditService:
    """Service for writing and reading audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def log_action(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str],
        user_id: Optional[int],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Persist an audit log entry."""
        serialized = None
        if metadata is not None:
            try:
                import json

                serialized = json.dumps(metadata, default=str)
            except Exception:
                serialized = str(metadata)

        entry = AuditLog(
            action=action,
            resource=resource,
            resource_id=resource_id,
            user_id=user_id,
            meta=serialized,
            created_at=datetime.utcnow(),
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        resource: Optional[str] = None,
    ) -> Tuple[List[AuditLog], int]:
        """List audit log entries with pagination."""
        query = self.db.query(AuditLog).order_by(AuditLog.created_at.desc())
        if resource:
            query = query.filter(AuditLog.resource == resource)

        total = query.count()
        items = query.offset(offset).limit(limit).all()
        return items, total
