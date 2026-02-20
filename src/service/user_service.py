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


# =========================
# NUEVO: Requests de password
# =========================
@dataclass(frozen=True)
class AdminChangePasswordRequest:
    target_username: str
    new_password: str
    must_change_password: int = 0  # 1 = fuerza cambio en siguiente login (opcional)


@dataclass(frozen=True)
class ChangeOwnPasswordRequest:
    username: str
    current_password: str
    new_password: str


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

    def update_user(self, username: str, display_name: str, email: str | None, role_code: str, is_active: int) -> None:
        username = (username or "").strip()
        display_name = (display_name or "").strip()
        email = (email or "").strip() if email else None
        role_code = (role_code or "").strip().lower()

        if not username:
            raise UserServiceError("Username inválido.")
        if not display_name:
            raise UserServiceError("Display Name es requerido.")
        if role_code not in ("admin", "operator", "viewer"):
            raise UserServiceError("Role inválido.")

        self.user_repo.update_user(username, display_name, email if email else None, role_code, int(is_active))


    def reset_password(self, username: str, temp_password: str) -> None:
        username = (username or "").strip()
        temp_password = (temp_password or "").strip()

        if len(temp_password) < 8:
            raise UserServiceError("El password temporal debe tener al menos 8 caracteres.")

        hashed = self._argon2.hash(temp_password)
        self.user_repo.reset_password(username, hashed, "argon2id")

    # =========================
    # NUEVO: Cambiar password (admin) para cualquier usuario
    # =========================
    def admin_change_password(self, req: AdminChangePasswordRequest) -> None:
        target_username = (req.target_username or "").strip()
        new_password = (req.new_password or "").strip()
        must_change = int(req.must_change_password)

        if not target_username:
            raise UserServiceError("Username objetivo es requerido.")
        if len(new_password) < 8:
            raise UserServiceError("El nuevo password debe tener al menos 8 caracteres.")

        existing = self.user_repo.get_by_username(target_username)
        if not existing:
            raise UserServiceError("El usuario objetivo no existe.")

        hashed = self._argon2.hash(new_password)

        # OJO: este método es NUEVO en el repo (lo implementaremos después)
        # Debe actualizar password_hash/password_algo y opcionalmente must_change_password
        self.user_repo.update_password(
            username=target_username,
            password_hash=hashed,
            password_algo="argon2id",
            must_change_password=must_change,
        )

    # =========================
    # NUEVO: Cambiar tu propio password validando el actual
    # =========================
    def change_own_password(self, req: ChangeOwnPasswordRequest) -> None:
        username = (req.username or "").strip()
        current_password = (req.current_password or "").strip()
        new_password = (req.new_password or "").strip()

        if not username:
            raise UserServiceError("Username inválido.")
        if len(new_password) < 8:
            raise UserServiceError("El nuevo password debe tener al menos 8 caracteres.")
        if new_password == current_password:
            raise UserServiceError("El nuevo password debe ser diferente al actual.")

        user = self.user_repo.get_by_username(username)
        if not user:
            raise UserServiceError("Usuario no encontrado.")

        # Se asume que get_by_username devuelve password_hash y password_algo (o al menos password_hash)
        stored_hash = getattr(user, "password_hash", None)
        if not stored_hash:
            raise UserServiceError("No fue posible validar el password actual (hash no disponible).")

        # Verifica el password actual (argon2 levanta excepción si falla)
        try:
            self._argon2.verify(stored_hash, current_password)
        except Exception:
            raise UserServiceError("Password actual incorrecto.")

        # Rehash si el algoritmo/parámetros cambiaron (buena práctica)
        try:
            if self._argon2.check_needs_rehash(stored_hash):
                stored_hash = self._argon2.hash(current_password)
        except Exception:
            # si algo falla aquí no bloqueamos el cambio, solo seguimos
            pass

        new_hash = self._argon2.hash(new_password)

        # Al cambiar el propio password, normalmente must_change_password debe quedar en 0
        self.user_repo.update_password(
            username=username,
            password_hash=new_hash,
            password_algo="argon2id",
            must_change_password=0,
        )