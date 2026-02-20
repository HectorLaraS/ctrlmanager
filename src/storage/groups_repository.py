from dataclasses import dataclass
from typing import List, Optional, Any, Dict

from src.storage.database import Database


@dataclass(frozen=True)
class GroupInfo:
    group_code: str
    group_name: str
    service_name: str


class GroupsRepository:
    def __init__(self, db: Database, audit_repo=None):
        self.db = db
        self.audit_repo = audit_repo
        self._actor_user_id: Optional[int] = None

    # ✅ Para no tocar tus vistas: MainWindow lo setea una vez.
    def set_actor(self, actor_user_id: Optional[int]) -> None:
        self._actor_user_id = int(actor_user_id) if actor_user_id is not None else None

    def list_groups(self, limit: int = 2000) -> List[GroupInfo]:
        sql = f"""
        SELECT TOP ({limit})
            GroupCode, GroupName, ServiceName
        FROM dbo.[Groups]
        ORDER BY GroupCode ASC;
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            rows = cur.execute(sql).fetchall()

        out: List[GroupInfo] = []
        for r in rows:
            out.append(
                GroupInfo(
                    group_code="" if r[0] is None else str(r[0]),
                    group_name="" if r[1] is None else str(r[1]),
                    service_name="" if r[2] is None else str(r[2]),
                )
            )
        return out

    def get_by_code(self, group_code: str) -> Optional[GroupInfo]:
        sql = """
        SELECT GroupCode, GroupName, ServiceName
        FROM dbo.[Groups]
        WHERE GroupCode = ?;
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            row = cur.execute(sql, (group_code,)).fetchone()

        if not row:
            return None

        return GroupInfo(
            group_code="" if row[0] is None else str(row[0]),
            group_name="" if row[1] is None else str(row[1]),
            service_name="" if row[2] is None else str(row[2]),
        )

    @staticmethod
    def _to_audit_dict(g: GroupInfo) -> Dict[str, Any]:
        return {
            "group_code": g.group_code,
            "group_name": g.group_name,
            "service_name": g.service_name,
        }

    @staticmethod
    def _diff_keys(old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
        keys = set(old.keys()) | set(new.keys())
        changed = []
        for k in keys:
            if old.get(k) != new.get(k):
                changed.append(k)
        return sorted(changed)

    def add_group(self, group_code: str, group_name: str, service_name: str) -> None:
        sql = """
        INSERT INTO dbo.[Groups] (GroupCode, GroupName, ServiceName, CreatedAtUtc)
        VALUES (?, ?, ?, GETUTCDATE());
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (group_code, group_name, service_name))
            conn.commit()

        # Audit (INSERT)
        if self.audit_repo is not None:
            new_obj = self.get_by_code(group_code)
            if new_obj:
                new_dict = self._to_audit_dict(new_obj)
                self.audit_repo.insert(
                    actor_user_id=self._actor_user_id,
                    action="INSERT",
                    entity_name="groups",
                    entity_id=str(group_code),
                    summary=f"Created group '{new_obj.group_name}' (code={new_obj.group_code})",
                    old_values=None,
                    new_values=new_dict,
                )

    def update_group(self, group_code: str, group_name: str, service_name: str) -> None:
        # Snapshot viejo para audit
        old_obj = self.get_by_code(group_code) if self.audit_repo is not None else None

        sql = """
        UPDATE dbo.[Groups]
        SET GroupName = ?, ServiceName = ?
        WHERE GroupCode = ?;
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (group_name, service_name, group_code))
            if cur.rowcount == 0:
                raise ValueError("No se actualizó ningún grupo (GroupCode no encontrado).")
            conn.commit()

        # Audit (UPDATE)
        if self.audit_repo is not None and old_obj is not None:
            new_obj = self.get_by_code(group_code)
            if new_obj:
                old_dict = self._to_audit_dict(old_obj)
                new_dict = self._to_audit_dict(new_obj)
                changed = self._diff_keys(old_dict, new_dict)

                # si no cambió nada, no auditamos
                if changed:
                    self.audit_repo.insert(
                        actor_user_id=self._actor_user_id,
                        action="UPDATE",
                        entity_name="groups",
                        entity_id=str(group_code),
                        summary=f"Updated group {group_code}: {', '.join(changed)}",
                        old_values=old_dict,
                        new_values=new_dict,
                    )