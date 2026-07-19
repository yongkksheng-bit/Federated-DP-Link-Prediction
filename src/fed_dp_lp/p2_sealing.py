"""Keyed commitments and one-way preparation helpers for P2 test sealing."""

from __future__ import annotations

import hashlib
import hmac
import io

import numpy as np
from cryptography.fernet import Fernet


def array_commitment(key: bytes, label: str, array: np.ndarray) -> str:
    digest = hmac.new(key, digestmod=hashlib.sha256)
    digest.update(label.encode())
    digest.update(str(array.dtype).encode())
    digest.update(str(array.shape).encode())
    digest.update(np.ascontiguousarray(array).tobytes())
    return digest.hexdigest()


def encrypted_npz(cipher: Fernet, **arrays: np.ndarray) -> bytes:
    stream = io.BytesIO()
    np.savez_compressed(stream, **arrays)
    return cipher.encrypt(stream.getvalue())
