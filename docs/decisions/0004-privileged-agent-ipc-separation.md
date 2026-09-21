# ADR 0004: Privileged Agent Service and Unprivileged UI Separation via Local IPC

## Status
Accepted

## Context
Workstations run user desktop sessions under unprivileged or semi-privileged student accounts. Sanitizing user data across protected directories (e.g. system trash, locked processes, other profile caches) requires elevated rights. However, running the graphical user interface as `root` / `Administrator` in an interactive user session is a severe security vulnerability (X11 hijacking, privilege escalation via GUI injection).

Furthermore, if the audit log and policy configuration files were accessible to the user running the UI, a malicious student could tamper with the cleaning rules or delete audit trails.

## Decision
We enforce a strict process boundary:
1. **Privileged Agent (`netejator98-agent`)**:
   - Runs as a system service / daemon (Windows Service, Linux systemd unit, macOS LaunchDaemon) with root/SYSTEM privileges.
   - Owns the protected directory (`/var/lib/Netejator98`, `%ProgramData%\Netejator98`, `/Library/Application Support/Netejator98`).
   - Owns the audit log, last-user store, and policy configuration.
   - Listens on a local IPC endpoint:
     - Linux / macOS: Unix domain socket with permissions `0660` and peer identity checks (`SO_PEERCRED`).
     - Windows: Named Pipe (`\\.\pipe\Netejator98Agent`) with explicit security descriptor restricting access to authenticated local users.
2. **Unprivileged UI (`netejator98-ui`)**:
   - Runs strictly within the student's graphical desktop session.
   - Collects user email input, sends identification requests over IPC, and displays sanitisation progress.
   - Possesses zero filesystem permissions over audit logs, private key blobs, or cleaning policies.

## Consequences
- **Positive**: Complete defense-in-depth: GUI vulnerabilities cannot lead to root compromise; students cannot tamper with logs or policy files.
- **Negative**: Requires OS-specific service installation and IPC protocol serialization.

