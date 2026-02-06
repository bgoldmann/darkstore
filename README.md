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
| `STORE_PLATFORM_PGP_PUBLIC_KEY` | — | Platform PGP public key (for Escrow policy page) |
| `STORE_PLATFORM_PGP_PUBLIC_KEY_PATH` | — | Path to file with platform PGP key |
| `STORE_ESCROW_AUTO_FINALIZE_DAYS` | 14 | Days until escrow may auto-release to seller |

## Migration (existing DB)

If you have an existing database, run the escrow migration once to add new columns:

```bash
cd store && python3 -m migrations.001_escrow_schema
```

(Requires venv with dependencies installed.)

## Roles

- **buyer:** Register, browse, cart, checkout, view own orders; escrow (report payment, confirm release, open dispute); set PGP in Profile.
- **seller:** Add/edit/delist products; see own listings and orders where they are primary seller; open dispute.
- **support:** Manage orders (status, notes); mark escrow funded; resolve disputes (release to seller or buyer).
- **admin:** Full access.

First seller/admin accounts must be created by setting `role` in the database (e.g. after registering as buyer).

## Runbooks

See [runbooks/](runbooks/).
