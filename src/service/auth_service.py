from dataclasses import dataclass

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHash

from src.storage.user_repository import UserRepository


class AuthError(Exception):
    pass


@dataclass(frozen=True)
class AuthResult:
    username: str
    role_code: str
    must_change_password: bool


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self._argon2 = PasswordHasher()

    def login(self, username: str, password: str) -> AuthResult:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise AuthError("Usuario o password inválidos")

        if not user.is_active:
            raise AuthError("Usuario inactivo")

        if not self._verify_password(password, user.password_hash, user.password_algo):
            raise AuthError("Usuario o password inválidos")

        return AuthResult(
            username=user.username,
            role_code=(user.role_code or "").lower(),
            must_change_password=user.must_change_password
        )


    def _verify_password(self, plain: str, stored_hash: str, algo: str) -> bool:
        if not stored_hash:
            return False

        algo = (algo or "").lower().strip()

        # Argon2id (tu caso)
        if algo in ("argon2", "argon2id"):
            try:
                return self._argon2.verify(stored_hash, plain)
            except (VerifyMismatchError, InvalidHash):
                return False

        # bcrypt
        if stored_hash.startswith("$2"):
            try:
                return bcrypt.checkpw(plain.encode("utf-8"), stored_hash.encode("utf-8"))
            except Exception:
                return False

        # fallback: plain (solo para etapas tempranas si decides usarlo)
        return plain == stored_hash


    def change_password(self, username: str, new_password: str) -> None:
        new_password = (new_password or "").strip()

        # Reglas mínimas (ajústalas a tu gusto)
        if len(new_password) < 8:
            raise AuthError("El password debe tener al menos 8 caracteres.")

        # hash Argon2id
        new_hash = self._argon2.hash(new_password)

        # update en DB + must_change_password = 0
        # CAMBIO MINIMO: usar firma nueva del repo
        self.user_repo.update_password(
            username=username,
            password_hash=new_hash,
            password_algo="argon2id",
            must_change_password=0,
        )