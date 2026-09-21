# ADR 0003: Asymmetric Audit Log Encryption and Ciphertext Hash Chaining

## Status
Accepted

## Context
Workstations run continuously unattended with students logged in. An audit log must record all login events, outcomes, and sanitisation operations. If symmetric encryption using a password-derived key were used, the decryption key (or password) would have to reside in memory or disk on the client machine, exposing past audit history to any local user or student gaining administrative rights.

Furthermore, administrators need to be able to verify whether the log has been truncated, reordered, or modified without needing to supply the administrative password.

## Decision
1. **Asymmetric Write-Only Sealing**:
   - On initial setup, an X25519 keypair is generated.
   - The **Public Key** is stored in the clear in the protected system directory (`/var/lib/Netejator98/log_public.key`). The background agent seals audit records using libsodium anonymous sealed boxes (`crypto_box_seal` via `PyNaCl`).
   - The agent possesses **no knowledge of the private key** during normal operation. Possessing the public key allows write-only encryption.
   - The **Private Key** is encrypted at rest using an authenticated symmetric key (XSalsa20-Poly1305 / `SecretBox`) derived from the administrator's password using Argon2id with a unique 32-byte salt.
   - The private key is only unwrapped in memory in the privileged agent when an authenticated administrator initiates an audit inspection session, and is immediately purged upon session closure.
2. **Ciphertext Hash Chaining**:
   - Each audit log line on disk is structured as:
     `{"seq": n, "sealed": "<base64>", "prev_hash": "<hex>", "entry_hash": "<hex>"}`
   - `entry_hash = SHA256(f"{seq}:{prev_hash}:{sealed}")`
   - Because the hash chain is computed over the **ciphertext**, integrity verification (`verify-audit`) can be performed unauthenticated without decrypting the data.
3. **Atomic Key Re-Wrapping on Password Change**:
   - When the administrator changes their password, only the private key wrapper blob is re-encrypted with the new Argon2id KEK. Past log entries do not require re-encryption, eliminating corruption risks during password updates.
4. **Offline Recovery Key**:
   - At setup time, an optional high-entropy recovery key can wrap a second copy of the private key, permitting recovery if the password is lost.

## Consequences
- **Positive**: Complete defense against compromise: students or attackers gaining physical or local admin access cannot read historical student emails or logs.
- **Positive**: Hash chain verification runs offline without credentials.
- **Negative**: If the administrator forgets the password and has no recovery key, the logs are mathematically unrecoverable by design.

