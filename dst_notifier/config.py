from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import yaml
from cryptography.fernet import Fernet

ETC_DIR = Path("etc")
CONFIG_FILE = ETC_DIR / "config.yaml"


def _config_error(message: str) -> None:
    print(f"Error: {message}")
    sys.exit(1)


def _require_mapping(data: dict[str, Any], key: str, where: str) -> dict[str, Any]:
    raw = data.get(key)
    if not isinstance(raw, dict):
        _config_error(f"missing or invalid '{key}' in {where} (expected a mapping).")
    return cast(dict[str, Any], raw)


def _require_str(d: dict[str, Any], key: str, where: str) -> str:
    v = d.get(key)
    if v is None:
        _config_error(f"missing '{key}' in {where}.")
    s = str(v).strip()
    if not s:
        _config_error(f"empty '{key}' in {where}.")
    return s


def _require_int(d: dict[str, Any], key: str, where: str) -> int:
    v = d.get(key)
    if v is None:
        _config_error(f"missing '{key}' in {where}.")
    try:
        return int(v)
    except (TypeError, ValueError):
        _config_error(f"invalid '{key}' in {where} (expected an integer).")


def _require_receivers(data: dict[str, Any]) -> list[str]:
    raw = data.get("receivers")
    if not isinstance(raw, list) or not raw:
        _config_error("missing or empty 'receivers' in config (expected a non-empty list).")
    out: list[str] = []
    for i, item in enumerate(raw):
        s = str(item).strip() if item is not None else ""
        if not s:
            _config_error(f"empty entry in 'receivers' at index {i}.")
        out.append(s)
    return out


@dataclass
class PathsConfig:
    secret_key: Path
    secret_password: Path
    state_file: Path

@dataclass
class SmtpConfig:
    server: str
    port: int
    sender_email: str


@dataclass
class NotificationConfig:
    days_before: int
    template: str


@dataclass
class AppConfig:
    paths: PathsConfig
    smtp: SmtpConfig
    receivers: list[str]
    language: str
    logging: dict[str, Any] | None
    notifications: list[NotificationConfig] = field(default_factory=list)


def _require_notifications(data: dict[str, Any]) -> list[NotificationConfig]:
    raw = data.get("notifications", [])
    if not isinstance(raw, list):
        _config_error("invalid 'notifications' in config (expected a list).")

    notifications: list[NotificationConfig] = []
    days_before_values: set[int] = set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            _config_error(f"invalid notification at index {i} (expected a mapping).")

        days_before = item.get("days_before")
        if type(days_before) is not int or days_before < 0:
            _config_error(
                f"invalid 'days_before' in notification at index {i} "
                "(expected a non-negative integer)."
            )
        if days_before in days_before_values:
            _config_error(f"duplicate 'days_before' value {days_before} in notifications.")
        days_before_values.add(days_before)

        template = _require_str(item, "template", f"notification at index {i}")
        notifications.append(NotificationConfig(days_before=days_before, template=template))

    return notifications


def load_config() -> AppConfig:
    if not CONFIG_FILE.exists():
        print(f"Error: {CONFIG_FILE} is missing. Please create it from config.example.yaml.")
        sys.exit(1)

    raw = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    data: dict[str, Any] = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

    logging_raw = data.get("logging")
    log_cfg: dict[str, Any] | None
    if logging_raw is None:
        log_cfg = None
    elif isinstance(logging_raw, dict):
        log_cfg = cast(dict[str, Any], logging_raw)
    else:
        _config_error("invalid 'logging' in config (expected a mapping).")

    paths_data = _require_mapping(data, "paths", "config")
    smtp_data = _require_mapping(data, "smtp", "config")

    receivers = _require_receivers(data)
    language = _require_str(data, "language", "config")
    notifications = _require_notifications(data)

    return AppConfig(
        paths=PathsConfig(
            secret_key=Path(_require_str(paths_data, "secret_key", "paths")),
            secret_password=Path(_require_str(paths_data, "secret_password", "paths")),
            state_file=Path(_require_str(paths_data, "state_file", "paths")),
        ),
        smtp=SmtpConfig(
            server=_require_str(smtp_data, "server", "smtp"),
            port=_require_int(smtp_data, "port", "smtp"),
            sender_email=_require_str(smtp_data, "sender_email", "smtp"),
        ),
        receivers=receivers,
        language=language,
        logging=log_cfg,
        notifications=notifications,
    )

def decrypt_password(config: AppConfig) -> str:
    """Decrypts the password using the local key file defined in config."""
    if not config.paths.secret_key.exists() or not config.paths.secret_password.exists():
        print("❌ Key or password not found. Please run 'uv run inv setup' first.")
        sys.exit(1)
        
    key = config.paths.secret_key.read_bytes()
    encrypted_password = config.paths.secret_password.read_bytes()
        
    fernet = Fernet(key)
    try:
        return fernet.decrypt(encrypted_password).decode("utf-8")
    except Exception:
        print("❌ Decryption error: Invalid key or corrupted password file.")
        sys.exit(1)
