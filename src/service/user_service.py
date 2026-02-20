# src/service/user_service.py
from dataclasses import dataclass
from typing import Optional

from argon2 import PasswordHasher

from src.storage.user_repository import UserRepository


class UserServiceError(Exception):
    pass


@dataclass(frozen=True)
class CreateUserRequest:
    username: str
    display_name: str
    email: Optional[str]
    role_code: str
    initial_password: str


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self._argon2 = PasswordHasher()

    def create_user(self, req: CreateUserRequest) -> None:
        username = (req.username or "").strip()
        display_name = (req.display_name or "").strip()
        email = (req.email or "").strip() if req.email else None
        role_code = (req.role_code or "").strip().lower()
        pw = (req.initial_password or "").strip()

        if not username:
            raise UserServiceError("Username es requerido.")
        if not display_name:
            raise UserServiceError("Display Name es requerido.")
        if role_code not in ("admin", "operator", "viewer"):
            raise UserServiceError("Role inválido. Usa admin/operator/viewer.")
        if len(pw) < 8:
            raise UserServiceError("El password inicial debe tener al menos 8 caracteres.")

        # Username único
        existing = self.user_repo.get_by_username(username)
        if existing:
            raise UserServiceError("Ese username ya existe.")

        # Hash Argon2id
        hashed = self._argon2.hash(pw)

        # Insert
        self.user_repo.add_user(
            username=username,
            display_name=display_name,
            email=email if email else None,
            password_hash=hashed,
            password_algo="argon2id",
            role_code=role_code,
            is_active=1,
            must_change_password=1,
        )