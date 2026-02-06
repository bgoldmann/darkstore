# Darkstore application

Tor onion e-commerce store backend and frontend. See project root [README.md](../README.md) and [tasks/prd-store.md](../tasks/prd-store.md).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export STORE_SECRET_KEY=your-secret-key
export STORE_SESSION_SECURE=false   # for local HTTP dev only
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Config (env)

| Variable | Default | Description |
|---------|---------|--------------|
| `STORE_SECRET_KEY` | (change in prod) | Session signing key |
| `STORE_HOST` | 127.0.0.1 | Bind address (localhost only for Tor) |
| `STORE_PORT` | 8000 | Port |
| `STORE_DATABASE_URL` | sqlite+aiosqlite:///./store.db | DB URL |
| `STORE_SESSION_SECURE` | true | Set false for local HTTP only |
| `STORE_PASSPHRASE_MIN_LENGTH` | 12 | Min passphrase length |
| `STORE_DEBUG` | false | Enable debug and /docs |

## Roles

- **buyer:** Register, browse, cart, checkout, view own orders.
- **seller:** Add/edit/delist products; see own listings.
- **support:** Manage orders (status, notes).
- **admin:** Full access.

First seller/admin accounts must be created by setting `role` in the database (e.g. after registering as buyer).

## Runbooks

See [runbooks/](runbooks/).
