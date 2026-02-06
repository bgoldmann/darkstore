# Escrow and disputes (US-020)

This runbook covers platform PGP key, dispute resolution, and logging policy for escrow. See also [docs/ESCROW_TOR_ONION_BEST_PRACTICES_2026.md](../../docs/ESCROW_TOR_ONION_BEST_PRACTICES_2026.md).

## Platform PGP key

- **Purpose:** Users verify signatures on official announcements and support messages. The key is displayed on the [Escrow & Dispute Policy](/policy/escrow) page.
- **Configuration:** Set either `STORE_PLATFORM_PGP_PUBLIC_KEY` (full ASCII-armored key string) or `STORE_PLATFORM_PGP_PUBLIC_KEY_PATH` (path to a file containing the key). Never log the key.
- **Rotation:** To rotate the key: generate a new key pair; update env or file; restart the app; publish the new public key on the policy page and inform users via a signed message with the **old** key if possible, then the new key for future messages.

## Time limits and auto-finalize

- **Auto-finalize:** Configurable via `STORE_ESCROW_AUTO_FINALIZE_DAYS` (default 14). After this many days from order creation, escrow may auto-release to the seller unless a dispute is opened.
- **Disputes** can only be opened before the auto-finalize timestamp. Support may extend escrow by updating `auto_finalize_at` in the database where appropriate (no UI for this in phase 1).

## Resolving disputes

- Only **support** and **admin** roles can mark orders as funded and resolve disputes (see [app/models/user.py](../app/models/user.py): `can_resolve_escrow_dispute()`).
- **Mark as funded:** When payment is confirmed (e.g. buyer reported and support verified), use "Mark as funded" on the admin order detail page. This sets `escrow_status` to `in_escrow`.
- **Resolve dispute:** When a dispute is open, use "Resolve: release to seller" or "Resolve: release to buyer" on the admin order detail page. This sets `escrow_status` and `dispute_resolution` accordingly.
- Evidence is sent by users encrypted to the platform PGP key (out-of-band or via support). Do not log dispute evidence or payment addresses.

## Logging (no escrow/payment data)

- Per [02-headers-logging.md](02-headers-logging.md): no payment details, no passphrases, no session tokens.
- **Do not log:** Escrow addresses, amounts, dispute evidence, or any data that links escrow actions to user identity beyond what is strictly required for order fulfillment. Log only high-level events (e.g. "escrow_status changed") if needed, without user or address details.

## Checklist (from escrow best practices)

- [ ] 2-of-3 multisig–friendly flow (platform never holds a single key).
- [ ] Monero preferred; if Bitcoin, mixing/CoinJoin encouraged.
- [ ] New address per transaction when live multisig is integrated.
- [ ] Mandatory PGP for escrow and dispute; platform key published and verifiable.
- [ ] Dispute policy documented (time limits, auto-finalize, evidence, mediator role).
- [ ] Escrow flows only over Tor; minimal logging; no payment/escrow data in logs.
