from dataclasses import dataclass
from typing import List, Optional

from src.storage.database import Database


@dataclass(frozen=True)
class GroupInfo:
    group_code: str
    group_name: str
    service_name: str


class GroupsRepository:
    def __init__(self, db: Database):
        self.db = db

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

    def add_group(self, group_code: str, group_name: str, service_name: str) -> None:
        sql = """
        INSERT INTO dbo.[Groups] (GroupCode, GroupName, ServiceName, CreatedAtUtc)
        VALUES (?, ?, ?, GETUTCDATE());
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (group_code, group_name, service_name))
            conn.commit()

    def update_group(self, group_code: str, group_name: str, service_name: str) -> None:
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
