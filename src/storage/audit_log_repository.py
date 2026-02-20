import json
import socket
import uuid
from typing import Any, Optional, Dict


class AuditLogRepository:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _default_host() -> Optional[str]:
        try:
            return socket.gethostname()
        except Exception:
            return None

    def insert(
        self,
        *,
        actor_user_id: Optional[int],
        action: str,                 # "INSERT" | "UPDATE"
        entity_name: str,            # "jobs" | "groups"
        entity_id: Optional[str],    # str(job_id) / str(group_id)
        summary: Optional[str],
        old_values: Optional[Dict[str, Any]],
        new_values: Optional[Dict[str, Any]],
        source_host: Optional[str] = None,
        source_ip: Optional[str] = None,
        correlation_id: Optional[uuid.UUID] = None,
    ) -> None:

        sql = """
        INSERT INTO dbo.wt_audit_log
        (
          actor_user_id, action, entity_name, entity_id,
          summary, old_values_json, new_values_json,
          source_host, source_ip, correlation_id
        )
        VALUES
        (
          ?, ?, ?, ?,
          ?, ?, ?,
          ?, ?, ?
        );
        """

        old_json = json.dumps(old_values, ensure_ascii=False) if old_values is not None else None
        new_json = json.dumps(new_values, ensure_ascii=False) if new_values is not None else None

        if correlation_id is None:
            correlation_id = uuid.uuid4()

        if source_host is None:
            source_host = self._default_host()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                actor_user_id,
                action,
                entity_name,
                entity_id,
                summary,
                old_json,
                new_json,
                source_host,
                source_ip,
                str(correlation_id),
            ))
            conn.commit()