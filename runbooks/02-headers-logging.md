# Headers and logging (US-002, US-003)

## Headers (US-002)

The application middleware strips or avoids:

- `Server`, `X-Powered-By`, `X-AspNet-*`, `X-Runtime`, `X-Version`, etc.

Only minimal safe headers are set (e.g. `X-Content-Type-Options: nosniff`). No OS, framework, or version in responses. Verify in browser dev tools that no identifying headers appear.

## Logging policy (US-003)

- **What is logged:** Request method, path, and response status code only. No request body, no passphrases, no session tokens, no payment details, no escrow addresses or amounts (US-003, US-020).
- **Retention:** Configure via logrotate or equivalent (e.g. 30 days); document in your runbook.
- **Storage:** Log files with restricted permissions (e.g. `700` or app user only). Prefer encrypted partition for logs if possible.
- **Production:** `STORE_DEBUG=false`; no verbose or stack-trace logging in production.

## Application config

- `STORE_LOG_LEVEL=INFO` (or `WARNING`).
- `STORE_LOG_PATH` optional; if set, logs to file (ensure directory and file permissions are restricted).
