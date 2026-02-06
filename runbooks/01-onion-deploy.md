# Onion service deployment (US-001)

## Prerequisites

- Tor from official repos, installed with GPG verification.
- Store app runs on `127.0.0.1:8000` (no clearnet listener).

## Tor v3 hidden service config

In `torrc` (or `/etc/tor/torrc`):

```
HiddenServiceDir /var/lib/tor/darkstore/
HiddenServicePort 80 127.0.0.1:8000
# Optional: HTTPS on same port if app serves TLS
# HiddenServicePort 443 127.0.0.1:8443
```

After starting Tor, the hostname is in `/var/lib/tor/darkstore/hostname` (v3 .onion address).

## Firewall

- Default deny incoming.
- Outbound allowed only to Tor network (e.g. Tor ports; no general internet).

## Verify

1. Start the store app: from `store/`, set `STORE_SECRET_KEY` and run `uvicorn app.main:app --host 127.0.0.1 --port 8000`.
2. Start Tor; ensure it reads the config above.
3. Open the .onion URL in Tor Browser; confirm the storefront loads.

## No clearnet

The store application must not listen on any non-localhost address. Binding to `127.0.0.1` only ensures all access is via the reverse path (Tor → local socket/port).
