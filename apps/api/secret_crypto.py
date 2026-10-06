from __future__ import annotations
import os,base64,hashlib
from cryptography.fernet import Fernet,InvalidToken

def _fernet()->Fernet:
    raw=os.getenv("GEOTECT_MASTER_KEY")
    if not raw:
        raise RuntimeError("GEOTECT_MASTER_KEY is required for API-secret encryption")
    # Accept a native Fernet key or derive one deterministically from a strong deployment secret.
    try:return Fernet(raw.encode())
    except Exception:
        key=base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
        return Fernet(key)

def encrypt_secret(value:str)->str:
    if not value: raise ValueError("Secret cannot be empty")
    return _fernet().encrypt(value.encode()).decode()

def decrypt_secret(value:str)->str:
    try:return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc: raise RuntimeError("Unable to decrypt secret with current master key") from exc

def masked_secret(last4:str)->str:
    return "••••••••"+last4
