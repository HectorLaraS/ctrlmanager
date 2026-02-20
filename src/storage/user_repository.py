import os
from dataclasses import dataclass
from typing import Optional, List

from src.storage.database import Database


@dataclass(frozen=True)
class UserRow:
    username: str
    display_name: str
    email: str
    role_code: str
    is_active: int
    must_change_password: int


@dataclass(frozen=True)
class UserRecord:
    user_id: int
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

        # ✅ NUEVO: columna user_id (default a tu tabla real)
        self.col_user_id = os.getenv("COL_USER_ID", "user_id").strip()

        self.col_user = os.getenv("COL_USERNAME", "username").strip()
        self.col_pass = os.getenv("COL_PASSWORD_HASH", "password_hash").strip()
        self.col_algo = os.getenv("COL_PASSWORD_ALGO", "password_algo").strip()
        self.col_must = os.getenv("COL_MUST_CHANGE", "must_change_password").strip()
        self.col_active = os.getenv("COL_IS_ACTIVE", "is_active").strip()
        self.col_role = os.getenv("COL_ROLE_CODE", "role_code").strip()

    def list_users(self, limit: int = 5000) -> List[UserRow]:
        sql = f"""
        SELECT TOP ({limit})
            username, display_name, ISNULL(email,''), role_code, is_active, must_change_password
        FROM {self.table}
        ORDER BY username ASC;
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            rows = cur.execute(sql).fetchall()

        out: List[UserRow] = []
        for r in rows:
            out.append(
                UserRow(
                    username="" if r[0] is None else str(r[0]),
                    display_name="" if r[1] is None else str(r[1]),
                    email="" if r[2] is None else str(r[2]),
                    role_code="" if r[3] is None else str(r[3]).lower(),
                    is_active=int(r[4]) if r[4] is not None else 1,
                    must_change_password=int(r[5]) if r[5] is not None else 0,
                )
            )
        return out

    def update_user(self, username: str, display_name: str, email: str | None, role_code: str, is_active: int) -> None:
        sql = f"""
        UPDATE {self.table}
        SET
            display_name = ?,
            email = ?,
            role_code = ?,
            is_active = ?
        WHERE username = ?;
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (display_name, email, role_code, int(is_active), username))
            if cur.rowcount == 0:
                raise ValueError("No se actualizó ningún usuario (username no encontrado).")
            conn.commit()

    def reset_password(self, username: str, password_hash: str, password_algo: str = "argon2id") -> None:
        sql = f"""
        UPDATE {self.table}
        SET
            password_hash = ?,
            password_algo = ?,
            must_change_password = 1
        WHERE username = ?;
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (password_hash, password_algo, username))
            if cur.rowcount == 0:
                raise ValueError("No se reseteó password (username no encontrado).")
            conn.commit()

    def get_by_username(self, username: str) -> Optional[UserRecord]:
        sql = f"""
        SELECT
            {self.col_user_id},
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
            user_id=int(row[0]) if row[0] is not None else 0,
            username="" if row[1] is None else str(row[1]),
            password_hash="" if row[2] is None else str(row[2]),
            password_algo="" if row[3] is None else str(row[3]).lower(),
            role_code="" if row[4] is None else str(row[4]).lower(),
            must_change_password=bool(row[5]) if row[5] is not None else False,
            is_active=bool(row[6]) if row[6] is not None else True,
        )

    # ==========================================================
    # NUEVO: update_password con firma compatible con UserService
    # ==========================================================
    def update_password(
        self,
        username: str,
        password_hash: str,
        password_algo: str = "argon2id",
        must_change_password: int = 0,
    ) -> None:
        """
        Actualiza password_hash/password_algo y setea must_change_password según se indique.
        - Para "change own password" normalmente must_change_password=0
        - Para "admin_change_password" puedes mandar 1 si quieres forzar cambio al login
        """
        sql = f"""
        UPDATE {self.table}
        SET
            {self.col_pass} = ?,
            {self.col_algo} = ?,
            {self.col_must} = ?
        WHERE {self.col_user} = ?;
        """

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (password_hash, password_algo, int(must_change_password), username))
            if cur.rowcount == 0:
                raise ValueError("No se actualizó password (username no encontrado).")
            conn.commit()

    # ==========================================================
    # (LEGACY) Tu método original preservado sin cambios de lógica
    # ==========================================================
    def _update_password_legacy(self, username: str, new_hash: str, algo: str = "argon2id") -> None:
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