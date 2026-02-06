# Incident response and compromise recovery (US-018)

## If compromise is suspected

1. **Bring system offline** (read-only if possible). Do not continue normal operation.
2. **Assume .onion keys may be compromised.** Plan to retire them.
3. **Forensics:** Preserve logs (per policy); inspect backend app, web server, and framework for signs of intrusion or tampering.
4. **Monitor descriptor usage** (e.g. via Onionprobe or Tor metrics) if you temporarily stop using the keys, to detect abuse.

## Recovery

1. **Generate new onion keys** (new HiddenServiceDir; see 03-key-backup.md).
2. **New HTTPS certificate** if applicable; update reverse proxy config.
3. **Update Onion-Location** if you serve it (e.g. clearnet counterpart).
4. **Inform users** via signed message (PGP or trusted channel) with the new .onion address and any impact summary.
5. **Optional:** Consider Onionbalance for key isolation in future deployments.

## Reference

- `docs/TOR_ONION_BEST_PRACTICES_2026.md` §8
- PRD US-018
