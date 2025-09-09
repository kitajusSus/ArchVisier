"""Minimal stub of :mod:`cryptography.fernet` for tests."""

class Fernet:
    def __init__(self, key: bytes) -> None:  # pragma: no cover - simple stub
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        return data

    def decrypt(self, token: bytes) -> bytes:
        return token

