"""X25519 asymmetric sealed box adapter using PyNaCl libsodium bindings."""

from __future__ import annotations

import base64
from typing import Optional, Tuple

import nacl.exceptions
import nacl.public

from netejator98.audit.domain.ports import EntryOpenerPort, EntrySealerPort
from netejator98.shared.errors import DomainError, OpeningError, SealingError
from netejator98.shared.result import Err, Ok, Result


class X25519SealAdapter(EntrySealerPort, EntryOpenerPort):
    """Adapter for write-only public key sealing and private key decryption."""

    def __init__(
        self,
        public_key: Optional[nacl.public.PublicKey] = None,
        private_key: Optional[nacl.public.PrivateKey] = None,
    ) -> None:
        self._public_key = public_key
        self._private_key = private_key
        if self._public_key is None and self._private_key is not None:
            self._public_key = self._private_key.public_key

    @classmethod
    def generate_keypair(cls) -> Tuple[bytes, bytes]:
        """Generate a new X25519 keypair, returning (public_bytes, private_bytes)."""
        priv = nacl.public.PrivateKey.generate()
        return bytes(priv.public_key), bytes(priv)

    @classmethod
    def from_public_key_bytes(cls, pub_bytes: bytes) -> X25519SealAdapter:
        """Create a write-only sealer using only the public key."""
        pk = nacl.public.PublicKey(pub_bytes)
        return cls(public_key=pk)

    @classmethod
    def from_private_key_bytes(cls, priv_bytes: bytes) -> X25519SealAdapter:
        """Create a full sealer/opener using the unwrapped private key."""
        sk = nacl.public.PrivateKey(priv_bytes)
        return cls(private_key=sk)

    def seal(self, plaintext: bytes) -> Result[str, DomainError]:
        """Seal plaintext using the public key alone (anonymous public key encryption)."""
        if self._public_key is None:
            return Err(SealingError("Public key is not configured for sealing"))
        try:
            box = nacl.public.SealedBox(self._public_key)
            ciphertext = box.encrypt(plaintext)
            b64_str = base64.b64encode(ciphertext).decode("ascii")
            return Ok(b64_str)
        except Exception as e:
            return Err(SealingError(f"Sealing failed: {e}"))

    def open(self, sealed_base64: str) -> Result[bytes, DomainError]:
        """Decrypt sealed ciphertext using the private key."""
        if self._private_key is None:
            return Err(OpeningError("Private key is not loaded in memory for decryption"))
        try:
            ciphertext = base64.b64decode(sealed_base64.encode("ascii"))
            box = nacl.public.SealedBox(self._private_key)
            plaintext = box.decrypt(ciphertext)
            return Ok(plaintext)
        except (nacl.exceptions.CryptoError, ValueError) as e:
            return Err(OpeningError(f"Decryption failed: {e}"))
        except Exception as e:
            return Err(OpeningError(f"Unexpected decryption failure: {e}"))

