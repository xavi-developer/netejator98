# Ubiquitous Language Glossary — Netejator98

This glossary establishes the formal domain terminology shared between developers, domain experts, school system administrators, and the software codebase. These terms must be used consistently across all code, tests, documentation, and user interfaces.

---

## 1. Access & Identity Context

| Term | Domain Classification | Definition |
| :--- | :--- | :--- |
| **InstitutionalEmail** | Value Object | A verified email address belonging strictly to the school's configured institutional domain (e.g., `@insestatut.cat`). Normalized to lowercase, immutable, and strictly validated. |
| **DomainPolicy** | Value Object | The operational rule specifying the authorized institutional domain suffix required for student desktop access. |
| **User** | Entity | An active student identity utilizing a workstation during a desktop session, bound to an `InstitutionalEmail`. |
| **LastUserRecord** | Value Object / Aggregate | A machine-scoped, privacy-preserving record of the most recent user who accessed the workstation. Stores the salted cryptographic hash of the email and the UTC login timestamp, never the plaintext email. |
| **UserChangeDecision** | Value Object | The result of comparing the newly entered user against the `LastUserRecord`. Enum values: `SAME_USER`, `DIFFERENT_USER`, `NO_PREVIOUS_USER`. |
| **UserChangeDetector** | Domain Service | Encapsulates the logic of evaluating whether sanitisation is required prior to granting desktop session access. |
| **AdminCredential** | Value Object | Credentials presented by an authorized system administrator (verified using Argon2id). |
| **AdminSession** | Entity / Value Object | A cryptographically validated, temporary in-memory authorization token permitting administrative operations (log inspection, policy update, password change). |
| **KioskPrompt** | Presentation Concept | The full-screen, frameless, always-on-top window that locks the desktop until valid institutional identification is provided. |

---

## 2. Sanitisation Context

| Term | Domain Classification | Definition |
| :--- | :--- | :--- |
| **CleaningPolicy** | Aggregate Root | The declarative policy defining the collection of cleaning targets, safety boundaries, deletion strategies, and profile management rules. |
| **CleaningTarget** | Entity | A specific category or surface of user-created or cached data designated for erasure (e.g., Downloads, Browser Profiles, Shell History). |
| **TargetCategory** | Enum / Value Object | High-level categorization of targets (`USER_DOCUMENTS`, `BROWSER_PROFILES`, `CACHES_AND_TEMP`, `CREDENTIALS`, `RECENT_FILES`, `CLOUD_SYNC`, `SHELL_HISTORY`, `TRASH`). |
| **PathPattern** | Value Object | A traversal-safe relative or anchored glob pattern targeting files or directories for erasure. Prohibits relative upward traversal (`..`) or unanchored global wildcards. |
| **ProtectedPathRule** | Value Object | A non-negotiable invariant boundary identifying paths that must never be modified or deleted (system directories, kernel roots, agent install directory, audit logs, administrator profile). |
| **SanitisationPlan** | Value Object | The fully resolved, ordered collection of concrete filesystem paths scheduled for removal after expanding targets and applying protected-path filters. |
| **PlannedDeletion** | Value Object | A single concrete file or directory slated for removal with its associated deletion strategy. |
| **DeletionStrategy** | Value Object | The method of removal: `STANDARD` (filesystem unlink/rmtree) or `SECURE` (zero/random overwrite prior to unlink). |
| **SanitisationOutcome** | Value Object | The comprehensive audit report produced at the conclusion of a sanitisation run, detailing targets processed, freed storage bytes, execution duration, and any non-fatal errors. |
| **BrowserProfile** | Value Object | Identifies the filesystem location and configuration files for a supported web browser (Chrome, Chromium, Edge, Firefox, Brave, Opera, Safari) across standard, Snap, Flatpak, or portable installs. |
| **SanitisationPlanner** | Domain Service | Expands a `CleaningPolicy` against platform-specific directories into an executable `SanitisationPlan`, guaranteeing invariant enforcement against `ProtectedPathRule`s. |

---

## 3. Audit & Cryptography Context

| Term | Domain Classification | Definition |
| :--- | :--- | :--- |
| **AuditEntry** | Value Object | The plaintext structured data record of a security-relevant event (`timestamp`, `machine_id`, `hostname`, `event_type`, `email`, `outcome`, `targets_cleaned`, `errors`). |
| **SealedEntry** | Value Object | An audit record encrypted using asymmetric anonymous public-key cryptography (X25519 `crypto_box_seal`). Write-only for the agent; cannot be read using the public key. |
| **HashChain** | Domain Service | Cryptographic sequence of entries where each entry's hash commits to the previous entry's ciphertext hash (`entry_hash = SHA256(seq:prev_hash:sealed)`). Tampering or deletion is detectable without decryption. |
| **AuditTrail** | Aggregate Root | Manages the append-only chronological log of `SealedEntry` records and guarantees hash-chain continuity and monotonic sequence ordering. |
| **EntrySealer** | Port (Interface) | Capability of sealing an `AuditEntry` using only the public key. |
| **EntryOpener** | Port (Interface) | Capability of decrypting a `SealedEntry` given an unwrapped private key held temporarily in memory. |
| **KeyWrapper** | Port (Interface) | Manages wrapping (encrypting) and unwrapping (decrypting) the X25519 private key using an Argon2id-derived Key Encryption Key (KEK). |
| **RecoveryKey** | Value Object | A high-entropy offline key allowing emergency unwrapping of the log's private key if the administrator password is forgotten. |
| **EscrowPublicKey** | Value Object | An optional secondary public key allowing central school-district IT to decrypt audit logs across multiple workstations. |

---

## 4. Architectural & System Primitives

| Term | Classification | Definition |
| :--- | :--- | :--- |
| **MachineId** | Value Object | An opaque, stable identifier representing the physical or virtual workstation hardware. |
| **Result[T, E]** | Shared Primitive | Functional monadic container representing either a successful calculation (`Ok[T]`) or an expected domain error (`Err[E]`). Eliminates unhandled domain exceptions. |
| **DomainEvent** | Shared Primitive | An immutable record of an important business occurrence within a bounded context (`UserIdentified`, `DifferentUserDetected`, `SanitisationCompleted`, etc.). |
| **PrivilegedAgent** | Process Architecture | The elevated background daemon (`netejator98-agent`) executing system-level operations, filesystem sanitisation, and append-only audit logging. |
| **PresentationUI** | Process Architecture | The unprivileged user-session application (`netejator98-ui`) displaying the kiosk prompt and administrative interface. |
| **AgentIPC** | Infrastructure | The local inter-process communication mechanism (Unix Domain Socket or Windows Named Pipe) with strict peer permission checking. |

