"""Argon2id password hasher implementation using PyNaCl libsodium bindings."""

from __future__ import annotations

import base64
import os
from typing import Tuple

import nacl.exceptions
import nacl.pwhash.argon2id

from netejator98.access.domain.repositories import PasswordHasherPort


class Argon2PasswordHasher(PasswordHasherPort):
    """Production password hasher utilizing native libsodium Argon2id."""

    def __init__(
        self,
        opslimit: int = nacl.pwhash.argon2id.OPSLIMIT_INTERACTIVE,
        memlimit: int = nacl.pwhash.argon2id.MEMLIMIT_INTERACTIVE,
    ) -> None:
        self._opslimit = opslimit
        self._memlimit = memlimit

    def hash_password(self, password: str) -> Tuple[str, str]:
        """Hash a password using Argon2id and return (verifier_str, salt_b64)."""
        pwd_bytes = password.encode("utf-8")
        hashed_bytes = nacl.pwhash.argon2id.str(
            pwd_bytes,
            opslimit=self._opslimit,
            memlimit=self._memlimit,
        )
        verifier_str = hashed_bytes.decode("ascii")
        # Extract a random salt identifier or generate a separate salt for KDF
        salt_bytes = os.urandom(16)
        salt_b64 = base64.b64encode(salt_bytes).decode("ascii")
        return verifier_str, salt_b64

    def verify_password(self, password: str, verifier: str) -> bool:
        """Verify a password against the Argon2id verifier string."""
        pwd_bytes = password.encode("utf-8")
        verifier_bytes = verifier.encode("ascii")
        try:
            return nacl.pwhash.argon2id.verify(verifier_bytes, pwd_bytes)
        except (nacl.exceptions.InvalidkeyError, nacl.exceptions.CryptoError):
            return False
        except Exception:
            return False

