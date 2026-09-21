# ADR 0001: Hexagonal Domain-Driven Design (DDD) Architecture

## Status
Accepted

## Context
Netejator98 is a security-sensitive, cross-platform workstation sanitization application running on Windows, Linux, and macOS in educational environments. The core business rules (user identity validation, change detection, sanitisation planning, safety boundaries, and cryptographic audit chains) must remain completely decoupled from operating system APIs, file system libraries, IPC mechanisms, and GUI frameworks.

## Decision
We adopt a strict layered/hexagonal Domain-Driven Design architecture with three distinct bounded contexts:
1. **Access Context**: Manages institutional email validation, user change detection, and administrator authentication.
2. **Sanitisation Context**: Manages declarative cleaning policies, target expansion, protected path safety invariants, and resilient deletion plans.
3. **Audit Context**: Manages tamper-evident hash chaining, asymmetric write-only encryption, and unauthenticated integrity verification.

### Rules Enforced
- **Zero OS Imports in Domain**: Domain models must only import standard library typing and dataclasses. No `os`, `sys`, `subprocess`, GUI, or network imports are permitted in `domain/`.
- **Ports & Adapters**: All external I/O (filesystems, clocks, credential managers, process managers) is defined as Python Protocols/ABCs in the application layer and implemented in `infrastructure/`.
- **Value Objects & Immutability**: All value objects are `@dataclass(frozen=True)` and self-validating in `__post_init__`.
- **Result Types**: Expected failures use `Result[T, E]` (`Ok` / `Err`) instead of unchecked exceptions.
- **In-Process Domain Events**: Contexts coordinate through asynchronous or synchronous domain events dispatched across an in-process `EventBus`.

## Consequences
- **Positive**: Complete unit testability using pure in-memory test doubles without filesystem or root privileges. High modularity and independent evolution of contexts.
- **Negative**: Additional boilerplate for mapping DTOs, domain events, and ports.

