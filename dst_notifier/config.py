from __future__ import annotations

import logging.config
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml
from cryptography.fernet import Fernet

ETC_DIR = Path("etc")
CONFIG_FILE = ETC_DIR / "config.yaml"

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
class AppConfig:
    paths: PathsConfig
    smtp: SmtpConfig
    receivers: list[str]
    language: str

def load_config() -> AppConfig:
    if not CONFIG_FILE.exists():
        print(f"Error: {CONFIG_FILE} is missing. Please create it from config.example.yaml.")
        sys.exit(1)

    raw = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8"))
    data: dict[str, Any] = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

    if "logging" in data:
        logging.config.dictConfig(data["logging"])

    paths_raw = data.get("paths", {})
    smtp_raw = data.get("smtp", {})
    paths_data: dict[str, Any] = cast(dict[str, Any], paths_raw) if isinstance(paths_raw, dict) else {}
    smtp_data: dict[str, Any] = cast(dict[str, Any], smtp_raw) if isinstance(smtp_raw, dict) else {}

    receivers_raw = data.get("receivers", [])
    receivers: list[str] = (
        [str(x) for x in receivers_raw]
        if isinstance(receivers_raw, list)
        else []
    )
    language = str(data.get("language") or "")

    return AppConfig(
        paths=PathsConfig(
            secret_key=Path(str(paths_data.get("secret_key", "var/secret_key"))),
            secret_password=Path(str(paths_data.get("secret_password", "var/secret_password"))),
            state_file=Path(str(paths_data.get("state_file", "var/state.json"))),
        ),
        smtp=SmtpConfig(
            server=str(smtp_data.get("server", "smtp.gmail.com")),
            port=int(smtp_data.get("port") or 587),
            sender_email=str(smtp_data.get("sender_email", "")),
        ),
        receivers=receivers,
        language=language,
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
