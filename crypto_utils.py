import base64
import hashlib
import hmac
import os
from typing import Tuple


def _derive_key(secret: str) -> bytes:
    return hashlib.sha256(secret.encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        block = hmac.new(key, nonce + counter.to_bytes(8, "big"), hashlib.sha256).digest()
        out.extend(block)
        counter += 1
    return bytes(out[:length])


def encrypt_text(plaintext: str, secret: str) -> str:
    key = _derive_key(secret)
    nonce = os.urandom(16)
    plain_bytes = plaintext.encode("utf-8")
    stream = _keystream(key, nonce, len(plain_bytes))
    cipher = bytes(p ^ s for p, s in zip(plain_bytes, stream))
    tag = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    payload = nonce + cipher + tag
    return base64.urlsafe_b64encode(payload).decode("ascii")


def decrypt_text(token: str, secret: str) -> str:
    key = _derive_key(secret)
    data = base64.urlsafe_b64decode(token.encode("ascii"))
    nonce, rest = data[:16], data[16:]
    cipher, tag = rest[:-32], rest[-32:]
    expected = hmac.new(key, nonce + cipher, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("Message altéré ou clé invalide")
    stream = _keystream(key, nonce, len(cipher))
    plain = bytes(c ^ s for c, s in zip(cipher, stream))
    return plain.decode("utf-8")
