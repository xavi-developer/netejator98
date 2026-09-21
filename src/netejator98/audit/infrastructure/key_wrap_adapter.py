"""Argon2id + SecretBox key wrapping adapter for protecting the X25519 private key."""

from __future__ import annotations

import os
import struct

import nacl.exceptions
import nacl.pwhash.argon2id
import nacl.secret
import nacl.utils

from netejator98.audit.domain.ports import KeyWrapperPort
from netejator98.shared.errors import DomainError, KeyUnwrapError
from netejator98.shared.result import Err, Ok, Result

MAGIC = b"N98K"
HEADER_FORMAT = ">4s16sII"  # Magic (4B), Salt (16B), opslimit (4B), memlimit (4B)
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


class Argon2KeyWrapAdapter(KeyWrapperPort):
    """Wraps and unwraps the private key at rest using Argon2id KEK and XSalsa20-Poly1305."""

    def __init__(
        self,
        opslimit: int = nacl.pwhash.argon2id.OPSLIMIT_INTERACTIVE,
        memlimit: int = nacl.pwhash.argon2id.MEMLIMIT_INTERACTIVE,
    ) -> None:
        self._opslimit = opslimit
        self._memlimit = memlimit

    def _derive_kek(self, password: str, salt: bytes, opslimit: int, memlimit: int) -> bytes:
        return nacl.pwhash.argon2id.kdf(
            size=nacl.secret.SecretBox.KEY_SIZE,
            password=password.encode("utf-8"),
            salt=salt,
            opslimit=opslimit,
            memlimit=memlimit,
        )

    def wrap_key(self, private_key_bytes: bytes, password: str) -> Result[bytes, DomainError]:
        try:
            salt = nacl.utils.random(nacl.pwhash.argon2id.SALTBYTES)
            kek = self._derive_kek(password, salt, self._opslimit, self._memlimit)
            box = nacl.secret.SecretBox(kek)
            ciphertext = box.encrypt(private_key_bytes)
            header = struct.pack(HEADER_FORMAT, MAGIC, salt, self._opslimit, self._memlimit)
            return Ok(header + ciphertext)
        except Exception as e:
            return Err(DomainError(f"Failed to wrap private key: {e}"))

    def unwrap_key(self, wrapped_blob: bytes, password: str) -> Result[bytes, DomainError]:
        if len(wrapped_blob) < HEADER_SIZE:
            return Err(KeyUnwrapError("Invalid key wrapped blob: size too small"))

        try:
            magic, salt, opslimit, memlimit = struct.unpack(
                HEADER_FORMAT, wrapped_blob[:HEADER_SIZE]
            )
            if magic != MAGIC:
                return Err(KeyUnwrapError("Invalid key wrapped blob header format"))

            ciphertext = wrapped_blob[HEADER_SIZE:]
            kek = self._derive_kek(password, salt, opslimit, memlimit)
            box = nacl.secret.SecretBox(kek)
            decrypted = box.decrypt(ciphertext)
            return Ok(decrypted)
        except (nacl.exceptions.CryptoError, ValueError) as e:
            return Err(KeyUnwrapError("Incorrect administrator password or corrupted key blob"))
        except Exception as e:
            return Err(KeyUnwrapError(f"Key unwrapping error: {e}"))

    def wrap_with_recovery_key(
        self, private_key_bytes: bytes, recovery_key: str
    ) -> Result[bytes, DomainError]:
        """Wrap private key using high-entropy recovery key."""
        return self.wrap_key(private_key_bytes, recovery_key)

    def unwrap_with_recovery_key(
        self, wrapped_blob: bytes, recovery_key: str
    ) -> Result[bytes, DomainError]:
        """Unwrap private key using high-entropy recovery key."""
        return self.unwrap_key(wrapped_blob, recovery_key)

