# Encrypted .onion key backup and recovery (US-015)

## Backup

1. Stop Tor so keys are not in use.
2. Copy the hidden service directory (e.g. `/var/lib/tor/darkstore/`) to a secure, encrypted location (e.g. LUKS volume or encrypted backup).
3. Do **not** store the main keys in CI or unencrypted deployment channels. Deployment docs (e.g. Ansible) must warn against unencrypted key handling.

## Recovery (key loss or compromise)

1. Bring the service offline (read-only if possible).
2. Assume .onion keys may be compromised; do not reuse them for the same service identity.
3. Generate new keys (new `HiddenServiceDir` or remove old dir and let Tor create new keys).
4. If using HTTPS: obtain a new certificate; update config.
5. Update Onion-Location header if you have a clearnet counterpart.
6. Inform users via a signed message (e.g. from a known PGP key or operator channel).

## Reference

- Tor Project: [Onion service key management](https://community.torproject.org/onion-services/)
- PRD US-015, US-018.
