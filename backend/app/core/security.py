"""
Cryptographic security, credential encryption, key masking, and idempotency protection.
"""
import base64
import hashlib
import hmac
import time
from typing import Dict, Optional, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings


def _derive_fernet_key(secret: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"quant_platform_salt_v1",
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


_CIPHER_KEY = _derive_fernet_key(settings.SECRET_KEY)
_CIPHER = Fernet(_CIPHER_KEY)


def encrypt_secret(plain_text: Optional[str]) -> Optional[str]:
    if not plain_text:
        return None
    try:
        return _CIPHER.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def decrypt_secret(cipher_text: Optional[str]) -> Optional[str]:
    if not cipher_text:
        return None
    try:
        return _CIPHER.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return None


def mask_key(key: Optional[str], visible_prefix: int = 4, visible_suffix: int = 4) -> str:
    if not key:
        return "Not Configured"
    if len(key) <= (visible_prefix + visible_suffix):
        return "****"
    return f"{key[:visible_prefix]}****{key[-visible_suffix:]}"


def generate_idempotency_key(symbol: str, side: str, strategy: str, rounded_timestamp: int) -> str:
    payload = f"{symbol}:{side}:{strategy}:{rounded_timestamp}"
    return hashlib.sha256(payload.encode()).hexdigest()


class IdempotencyGuard:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl_seconds = ttl_seconds
        self._seen_keys: Dict[str, float] = {}

    def check_and_set(self, key: str) -> bool:
        """
        Returns True if key is NEW and accepted.
        Returns False if key is a DUPLICATE within TTL.
        """
        now = time.time()
        self._cleanup(now)
        if key in self._seen_keys:
            return False
        self._seen_keys[key] = now
        return True

    def _cleanup(self, now: float):
        expired = [k for k, t in self._seen_keys.items() if now - t > self.ttl_seconds]
        for k in expired:
            del self._seen_keys[k]


idempotency_guard = IdempotencyGuard(ttl_seconds=60)


def compute_audit_hash(record_dict: dict, previous_hash: str = "GENESIS") -> str:
    import json
    data_str = json.dumps(record_dict, sort_keys=True) + f":{previous_hash}"
    return hashlib.sha256(data_str.encode("utf-8")).hexdigest()
