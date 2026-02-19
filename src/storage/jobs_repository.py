from dataclasses import dataclass
from typing import List, Optional

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
    def __init__(self, db: Database):
        self.db = db

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
