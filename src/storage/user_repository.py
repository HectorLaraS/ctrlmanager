import os
from dataclasses import dataclass
from typing import Optional

from src.storage.database import Database


@dataclass(frozen=True)
class UserRecord:
    username: str
    password_hash: str
    password_algo: str
    role_code: str
    must_change_password: bool
    is_active: bool


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

        self.table = os.getenv("USERS_TABLE", "dbo.wt_users").strip()
        self.col_user = os.getenv("COL_USERNAME", "username").strip()
        self.col_pass = os.getenv("COL_PASSWORD_HASH", "password_hash").strip()
        self.col_algo = os.getenv("COL_PASSWORD_ALGO", "password_algo").strip()
        self.col_must = os.getenv("COL_MUST_CHANGE", "must_change_password").strip()
        self.col_active = os.getenv("COL_IS_ACTIVE", "is_active").strip()
        self.col_role = os.getenv("COL_ROLE_CODE", "role_code").strip()


    def get_by_username(self, username: str) -> Optional[UserRecord]:
        sql = f"""
        SELECT
            {self.col_user},
            {self.col_pass},
            {self.col_algo},
            {self.col_role},
            {self.col_must},
            {self.col_active}
        FROM {self.table}
        WHERE {self.col_user} = ?
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            row = cur.execute(sql, (username,)).fetchone()

        if not row:
            return None

        return UserRecord(
            username="" if row[0] is None else str(row[0]),
            password_hash="" if row[1] is None else str(row[1]),
            password_algo="" if row[2] is None else str(row[2]).lower(),
            role_code="" if row[3] is None else str(row[3]).lower(),
            must_change_password=bool(row[4]) if row[4] is not None else False,
            is_active=bool(row[5]) if row[5] is not None else True,
        )
    
    def update_password(self, username: str, new_hash: str, algo: str = "argon2id") -> None:
        # Nota: usamos parámetros para valores, pero tabla/columnas vienen del env
        sql = f"""
        UPDATE {self.table}
        SET
            {self.col_pass} = ?,
            {self.col_algo} = ?,
            {self.col_must} = 0
        WHERE {self.col_user} = ?
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (new_hash, algo, username))
            if cur.rowcount == 0:
                raise ValueError("No se actualizó ningún usuario (username no encontrado).")
            conn.commit()

    def add_user(
        self,
        username: str,
        display_name: str,
        email: str | None,
        password_hash: str,
        password_algo: str,
        role_code: str,
        is_active: int = 1,
        must_change_password: int = 1,
    ) -> None:
        # Nota: usamos la tabla real por env (USERS_TABLE)
        # y las columnas reales si ya las mapeaste.
        # Para este insert usamos nombres estándar de tu tabla wt_users.
        sql = f"""
        INSERT INTO {self.table} (
            username,
            display_name,
            email,
            password_hash,
            password_algo,
            role_code,
            is_active,
            must_change_password
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                sql,
                (
                    username,
                    display_name,
                    email,
                    password_hash,
                    password_algo,
                    role_code,
                    int(is_active),
                    int(must_change_password),
                ),
            )
            conn.commit()

