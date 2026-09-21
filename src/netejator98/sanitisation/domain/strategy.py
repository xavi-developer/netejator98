"""DeletionStrategy enum defining standard vs secure deletion."""

from __future__ import annotations

from enum import Enum


class DeletionStrategy(str, Enum):
    """Strategy for sanitising files and directories."""

    STANDARD = "STANDARD"              # Standard file unlink / directory removal
    SECURE = "SECURE"                  # Overwrite contents with zeros prior to unlink (1-pass shred)
    TRUNCATE = "TRUNCATE"              # Truncate file to 0 bytes without removing file (history, logs)
    PURGE_CHILDREN = "PURGE_CHILDREN"  # Wipe directory contents while preserving parent folder structure
    SHRED_NIST = "SHRED_NIST"          # Multi-pass secure overwrite (zeros, ones, random) for credentials
    EMPTY_TRASH = "EMPTY_TRASH"        # Recycle bin / Trash purge strategy
    BROWSER_CLEAN = "BROWSER_CLEAN"    # Browser cache, cookie, and session cleanup
    CLOUD_WIPE = "CLOUD_WIPE"          # Cloud sync cache and local state removal
    GOLDEN_RESET = "GOLDEN_RESET"      # Revert target to clean golden template
    CUSTOM_CLEAN = "CUSTOM_CLEAN"      # User-defined custom sanitisation


