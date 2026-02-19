from dataclasses import dataclass
from typing import List

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
