# Store configuration – env and defaults; no secrets in repo.
from __future__ import annotations

import os
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name, "").lower()
    return v in ("1", "true", "yes") if default is False else v not in ("0", "false", "no", "")


class Settings:
    """Application settings from environment (STORE_*)."""

    def __init__(self) -> None:
        self.app_name: str = _env("STORE_APP_NAME", "Darkstore")
        self.debug: bool = _env_bool("STORE_DEBUG", False)
        self.host: str = _env("STORE_HOST", "127.0.0.1")
        self.port: int = _env_int("STORE_PORT", 8000)
        self.database_url: str = _env("STORE_DATABASE_URL", "sqlite+aiosqlite:///./store.db")
        self.secret_key: str = _env("STORE_SECRET_KEY", "CHANGE_IN_PRODUCTION_use_env_SECRET_KEY")
        self.session_cookie_name: str = _env("STORE_SESSION_COOKIE_NAME", "session")
        self.session_ttl_seconds: int = _env_int("STORE_SESSION_TTL_SECONDS", 86400 * 7)
        self.session_same_site: str = _env("STORE_SESSION_SAME_SITE", "lax")
        self.session_secure: bool = _env_bool("STORE_SESSION_SECURE", True)
        self.passphrase_min_length: int = _env_int("STORE_PASSPHRASE_MIN_LENGTH", 12)
        self.passphrase_require_upper: bool = _env_bool("STORE_PASSPHRASE_REQUIRE_UPPER", True)
        self.passphrase_require_lower: bool = _env_bool("STORE_PASSPHRASE_REQUIRE_LOWER", True)
        self.passphrase_require_digit: bool = _env_bool("STORE_PASSPHRASE_REQUIRE_DIGIT", True)
        self.passphrase_require_special: bool = _env_bool("STORE_PASSPHRASE_REQUIRE_SPECIAL", True)
        self.upload_dir: Path = Path(_env("STORE_UPLOAD_DIR", "./uploads")).resolve()
        self.upload_max_size_mb: int = _env_int("STORE_UPLOAD_MAX_SIZE_MB", 10)
        self.allowed_image_extensions: tuple[str, ...] = (".jpg", ".jpeg", ".png", ".gif", ".webp")
        self.log_level: str = _env("STORE_LOG_LEVEL", "INFO")
        self.log_path: str | None = os.getenv("STORE_LOG_PATH") or None
        # Platform PGP public key for escrow/support; verify signatures on official messages (US-020).
        # Set STORE_PLATFORM_PGP_PUBLIC_KEY (full ASCII-armored key) or STORE_PLATFORM_PGP_PUBLIC_KEY_PATH (file path).
        self.platform_pgp_public_key: str | None = os.getenv("STORE_PLATFORM_PGP_PUBLIC_KEY") or None
        self.platform_pgp_public_key_path: str | None = os.getenv("STORE_PLATFORM_PGP_PUBLIC_KEY_PATH") or None
        self.escrow_auto_finalize_days: int = _env_int("STORE_ESCROW_AUTO_FINALIZE_DAYS", 14)

    def get_platform_pgp_public_key(self) -> str | None:
        """Return platform PGP public key (from env or from file). Used for Escrow policy page; never logged."""
        if self.platform_pgp_public_key:
            return self.platform_pgp_public_key.strip()
        if self.platform_pgp_public_key_path:
            try:
                with open(self.platform_pgp_public_key_path, "r") as f:
                    return f.read().strip()
            except OSError:
                return None
        return None


def get_settings() -> Settings:
    return Settings()
