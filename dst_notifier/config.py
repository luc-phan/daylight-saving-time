import yaml
import logging.config
from pathlib import Path
import sys
from cryptography.fernet import Fernet
from dataclasses import dataclass

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
    
    data = yaml.safe_load(CONFIG_FILE.read_text(encoding="utf-8")) or {}
    
    if "logging" in data:
        logging.config.dictConfig(data["logging"])
        
    paths_data = data.get("paths", {})
    smtp_data = data.get("smtp", {})
    receivers = data.get("receivers", [])
    language = data.get("language")
    
    return AppConfig(
        paths=PathsConfig(
            secret_key=Path(paths_data.get("secret_key", "var/secret_key")),
            secret_password=Path(paths_data.get("secret_password", "var/secret_password")),
            state_file=Path(paths_data.get("state_file", "var/state.json")),
        ),
        smtp=SmtpConfig(
            server=smtp_data.get("server", "smtp.gmail.com"),
            port=smtp_data.get("port", 587),
            sender_email=smtp_data.get("sender_email", "")
        ),
        receivers=receivers,
        language=language
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
    except Exception as e:
        print("❌ Decryption error: Invalid key or corrupted password file.")
        sys.exit(1)
