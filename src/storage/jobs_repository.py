from dataclasses import dataclass
from typing import List, Optional, Any, Dict

from src.storage.database import Database


@dataclass(frozen=True)
class JobInfo:
    id: int
    type: str
    job_name: str
    group_code: str
    group_name: str
    service_name: str
    severity: str
    created_at_utc: str


class JobsRepository:
    def __init__(self, db: Database, audit_repo=None):
        self.db = db
        self.audit_repo = audit_repo
        self._actor_user_id: Optional[int] = None

    # ✅ Para no tocar tus vistas: MainWindow lo setea una vez.
    def set_actor(self, actor_user_id: Optional[int]) -> None:
        self._actor_user_id = int(actor_user_id) if actor_user_id is not None else None

    def list_jobs(self, search: Optional[str] = None, limit: int = 2000) -> List[JobInfo]:
        # LEFT JOIN para que si no existe el grupo, el job igual aparezca
        if search:
            sql = f"""
            SELECT TOP ({limit})
                j.Id,
                j.Type,
                j.JobName,
                j.GroupCode,
                ISNULL(g.GroupName, '') AS GroupName,
                ISNULL(g.ServiceName, '') AS ServiceName,
                j.Severity,
                j.CreatedAtUtc
            FROM dbo.Jobs_information AS j
            LEFT JOIN dbo.[Groups] AS g
                ON g.GroupCode = j.GroupCode
            WHERE
                j.JobName LIKE ?
                OR j.GroupCode LIKE ?
                OR g.GroupName LIKE ?
                OR g.ServiceName LIKE ?
            ORDER BY j.CreatedAtUtc DESC;
            """
            like = f"%{search}%"
            params = (like, like, like, like)
        else:
            sql = f"""
            SELECT TOP ({limit})
                j.Id,
                j.Type,
                j.JobName,
                j.GroupCode,
                ISNULL(g.GroupName, '') AS GroupName,
                ISNULL(g.ServiceName, '') AS ServiceName,
                j.Severity,
                j.CreatedAtUtc
            FROM dbo.Jobs_information AS j
            LEFT JOIN dbo.[Groups] AS g
                ON g.GroupCode = j.GroupCode
            ORDER BY j.CreatedAtUtc DESC;
            """
            params = ()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            rows = cur.execute(sql, params).fetchall()

        out: List[JobInfo] = []
        for r in rows:
            out.append(
                JobInfo(
                    id=int(r[0]),
                    type="" if r[1] is None else str(r[1]),
                    job_name="" if r[2] is None else str(r[2]),
                    group_code="" if r[3] is None else str(r[3]),
                    group_name="" if r[4] is None else str(r[4]),
                    service_name="" if r[5] is None else str(r[5]),
                    severity="" if r[6] is None else str(r[6]),
                    created_at_utc="" if r[7] is None else str(r[7]),
                )
            )
        return out

    # ✅ Nuevo: para audit (old/new)
    def get_by_id(self, job_id: int) -> Optional[JobInfo]:
        sql = """
        SELECT
            j.Id,
            j.Type,
            j.JobName,
            j.GroupCode,
            ISNULL(g.GroupName, '') AS GroupName,
            ISNULL(g.ServiceName, '') AS ServiceName,
            j.Severity,
            j.CreatedAtUtc
        FROM dbo.Jobs_information AS j
        LEFT JOIN dbo.[Groups] AS g
            ON g.GroupCode = j.GroupCode
        WHERE j.Id = ?;
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            row = cur.execute(sql, (int(job_id),)).fetchone()

        if not row:
            return None

        return JobInfo(
            id=int(row[0]),
            type="" if row[1] is None else str(row[1]),
            job_name="" if row[2] is None else str(row[2]),
            group_code="" if row[3] is None else str(row[3]),
            group_name="" if row[4] is None else str(row[4]),
            service_name="" if row[5] is None else str(row[5]),
            severity="" if row[6] is None else str(row[6]),
            created_at_utc="" if row[7] is None else str(row[7]),
        )

    @staticmethod
    def _to_audit_dict(j: JobInfo) -> Dict[str, Any]:
        return {
            "id": j.id,
            "type": j.type,
            "job_name": j.job_name,
            "group_code": j.group_code,
            "group_name": j.group_name,
            "service_name": j.service_name,
            "severity": j.severity,
            "created_at_utc": j.created_at_utc,
        }

    @staticmethod
    def _diff_keys(old: Dict[str, Any], new: Dict[str, Any]) -> List[str]:
        keys = set(old.keys()) | set(new.keys())
        changed = []
        for k in keys:
            if old.get(k) != new.get(k):
                changed.append(k)
        return sorted(changed)

    def add_job(self, type_: str, job_name: str, group_code: str, severity: str) -> int:
        sql = """
        INSERT INTO dbo.Jobs_information (Type, JobName, GroupCode, Severity, CreatedAtUtc)
        OUTPUT INSERTED.Id
        VALUES (?, ?, ?, ?, GETUTCDATE());
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            row = cur.execute(sql, (type_, job_name, group_code, severity)).fetchone()
            conn.commit()

        job_id = int(row[0]) if row and row[0] is not None else 0

        if self.audit_repo is not None and job_id:
            new_obj = self.get_by_id(job_id)
            if new_obj:
                new_dict = self._to_audit_dict(new_obj)
                self.audit_repo.insert(
                    actor_user_id=self._actor_user_id,
                    action="INSERT",
                    entity_name="jobs",
                    entity_id=str(job_id),
                    summary=f"Created job '{new_obj.job_name}' (group_code={new_obj.group_code})",
                    old_values=None,
                    new_values=new_dict,
                )

        return job_id

    def update_job(self, job_id: int, type_: str, job_name: str, group_code: str, severity: int) -> None:
        # Snapshot viejo para audit
        old_obj = self.get_by_id(job_id) if self.audit_repo is not None else None

        sql = """
        UPDATE dbo.Jobs_information
        SET
            Type = ?,
            JobName = ?,
            GroupCode = ?,
            Severity = ?
        WHERE Id = ?;
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (type_, job_name, group_code, int(severity), int(job_id)))
            if cur.rowcount == 0:
                raise ValueError("No se actualizó ningún registro (Id no encontrado).")
            conn.commit()

        # Audit (UPDATE)
        if self.audit_repo is not None and old_obj is not None:
            new_obj = self.get_by_id(job_id)
            if new_obj:
                old_dict = self._to_audit_dict(old_obj)
                new_dict = self._to_audit_dict(new_obj)
                changed = self._diff_keys(old_dict, new_dict)

                # si no cambió nada, no auditamos
                if changed:
                    self.audit_repo.insert(
                        actor_user_id=self._actor_user_id,
                        action="UPDATE",
                        entity_name="jobs",
                        entity_id=str(job_id),
                        summary=f"Updated job {job_id}: {', '.join(changed)}",
                        old_values=old_dict,
                        new_values=new_dict,
                    )