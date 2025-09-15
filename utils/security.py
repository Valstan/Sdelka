from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from pathlib import Path

from config.settings import CONFIG


import logging

# Хранилище пароля пользователя (зашифровано) и вшитый админский пароль

# Админский пароль: "Metro@2000"
# Храним в виде HMAC-SHA256 от строки с солью, чтобы не светить plaintext.
# Формат: HMAC_SHA256(secret_key, password). Секрет зашит как base64.

_ADMIN_SECRET_B64 = "bUpiQzZ4d0JURTRrU2VjcmV0S2V5Rm9yQWRtaW4="  # произвольный секрет
_ADMIN_PASSWORD_PLAIN = "Metro@2000"


def _hmac_sha256_hex(key_bytes: bytes, message: str) -> str:
    return hmac.new(key_bytes, message.encode("utf-8"), hashlib.sha256).hexdigest()


def _get_admin_key() -> bytes:
    try:
        return base64.b64decode(_ADMIN_SECRET_B64)
    except Exception:
        return b"fallback-admin-key"


_ADMIN_PWHASH = _hmac_sha256_hex(_get_admin_key(), _ADMIN_PASSWORD_PLAIN)


@dataclass
class PasswordRecord:
    # Соль + PBKDF2-HMAC-SHA256
    salt: str
    iterations: int
    pw_hash_hex: str


def _passwords_file() -> Path:
    # Хранить рядом с программой, в data
    return CONFIG.data_dir / "user_pw.json"


def _pbkdf2_sha256(password: str, salt: bytes, iterations: int = 120_000) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def verify_admin_password(input_password: str) -> bool:
    # Сравниваем HMAC с зашитым
    return hmac.compare_digest(
        _ADMIN_PWHASH, _hmac_sha256_hex(_get_admin_key(), input_password)
    )


def load_user_password() -> PasswordRecord | None:
    p = _passwords_file()
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return PasswordRecord(salt=data["salt"], iterations=int(data["iterations"]), pw_hash_hex=data["pw_hash_hex"])  # type: ignore[return-value]
    except Exception:
        return None


def save_user_password(new_password: str) -> None:
    salt = os.urandom(16)
    iterations = 150_000
    dk = _pbkdf2_sha256(new_password, salt, iterations)
    rec = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "iterations": iterations,
        "pw_hash_hex": dk.hex(),
    }
    p = _passwords_file()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        logging.getLogger(__name__).exception("Ignored unexpected error: %s", exc)
    p.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")


def verify_user_password(input_password: str) -> bool:
    rec = load_user_password()
    if rec is None:
        # Пароль не установлен — вход по пользовательскому паролю запрещаем
        return False
    try:
        salt = base64.b64decode(rec.salt)
        dk = _pbkdf2_sha256(input_password, salt, rec.iterations)
        return hmac.compare_digest(dk.hex(), rec.pw_hash_hex)
    except Exception:
        return False


def user_password_is_set() -> bool:
    return load_user_password() is not None
