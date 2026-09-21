# ADR 0005: Resilient Sanitisation Engine with Invariant Safety Boundaries

## Status
Accepted

## Context
Sanitising a shared workstation involves deleting diverse files across user profiles, browser data stores, credential caches, and temporary directories. The engine must:
1. Guarantee that no misconfiguration or malicious policy rule can ever delete operating system binaries, kernel files, Netejator98 program files, or administrator profiles.
2. Be resilient against locked files (e.g. background sync daemons, socket files, read-only permissions).
3. Provide an accurate Dry-Run mode for administrator policy verification.
4. Support optional secure overwrite deletion while remaining honest about modern solid-state drive (SSD) wear leveling and Copy-on-Write (CoW) filesystem limitations.

## Decision
1. **Immutable Invariant Safety Rules (`ProtectedPathRule`)**:
   - The engine defines hardcoded and configurable system boundaries (`/`, `/bin`, `/usr`, `/etc`, `/sbin`, `C:\Windows`, `C:\Program Files`, Netejator98 data dir, administrator user profile).
   - In both planning (`SanitisationPlanner`) and runtime execution (`ExecuteSanitisationUseCase`), any path that resolves to or is a parent of a protected path is immediately rejected and recorded as a policy violation. Deletion never proceeds on prohibited paths.
2. **Resilient Deletion Algorithm**:
   - Deletions are performed per-item with error capture. A locked file or permission error triggers permission reset (clearing read-only flags) and a retry loop (up to 3 attempts with brief backoff).
   - If a file remains locked, the error is recorded in the outcome report, but the sanitisation engine continues deleting the remaining targets without aborting the entire run.
3. **Dry-Run Mode**:
   - A dedicated `DryRunUseCase` resolves all targets against the current profile and outputs a `SanitisationPlan` showing exact paths and estimated bytes without modifying the filesystem.
4. **Secure Delete Transparency**:
   - When `secure_delete` is enabled, files are overwritten with zeros/random bytes before unlink. The documentation and user interface explicitly state that this is best-effort and does not guarantee unrecoverability on SSDs, NVMe drives, or CoW filesystems (btrfs, APFS, ZFS).

## Consequences
- **Positive**: Workstation availability is preserved even in the face of rogue policies or file locks. Accidental system damage is prevented by invariants.
- **Negative**: Best-effort secure deletion cannot guarantee forensic erasure without full disk wipe or OS reimaging.

