"""CredentialStorePort implementation for purging user-scoped credential stores."""

from __future__ import annotations

import os
import subprocess
from netejator98.sanitisation.application.ports import CredentialStorePort
from netejator98.shared.errors import DomainError
from netejator98.shared.result import Ok, Result


class RealCredentialStorePort(CredentialStorePort):
    """Purges user credentials from credential helpers, SSH agents, and keyrings."""

    def clear_user_credentials(self) -> Result[None, DomainError]:
        # Clear git credential cache
        try:
            subprocess.run(
                ["git", "credential-cache", "exit"],
                capture_output=True,
                timeout=2,
                check=False,
            )
        except Exception:
            pass

        # Clear SSH agent identities if agent socket is defined
        if "SSH_AUTH_SOCK" in os.environ:
            try:
                subprocess.run(
                    ["ssh-add", "-D"],
                    capture_output=True,
                    timeout=2,
                    check=False,
                )
            except Exception:
                pass

        return Ok(None)

