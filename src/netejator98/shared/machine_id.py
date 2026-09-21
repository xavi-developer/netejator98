"""Opaque MachineId value object representing unique workstation identity."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import platform
import uuid


@dataclass(frozen=True)
class MachineId:
    """Opaque, immutable workstation hardware identifier."""

    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned:
            raise ValueError("MachineId cannot be empty")
        object.__setattr__(self, "value", cleaned)

    def __str__(self) -> str:
        return self.value

    @classmethod
    def current(cls) -> MachineId:
        """Detect or synthesize a stable machine identifier across OS platforms."""
        # Try Linux /etc/machine-id
        for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            return cls(content)
                except OSError:
                    pass

        # Stable fallback based on node/processor/uuid
        node = platform.node() or "unknown-host"
        system = platform.system()
        mac = uuid.getnode()
        synthetic = hashlib.sha256(f"{node}:{system}:{mac}".encode("utf-8")).hexdigest()[:32]
        return cls(synthetic)

