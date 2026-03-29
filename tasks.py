import sys
import getpass
from invoke import task
from cryptography.fernet import Fernet

from dst_notifier.config import load_config
from dst_notifier.core import check_and_alert

@task
def setup(c):
    """
    Generates the encryption key, encrypts your SMTP password and saves it locally.
    """
    config = load_config()
    print("=== DST Notifier Configuration ===")
    
    if not config.paths.secret_key.exists():
        key = Fernet.generate_key()
        config.paths.secret_key.write_bytes(key)
        config.paths.secret_key.chmod(0o600)
        print(f"✅ Encryption key generated and secured in '{config.paths.secret_key}'.")
    else:
        key = config.paths.secret_key.read_bytes()
        print(f"ℹ️ Existing encryption key loaded from '{config.paths.secret_key}'.")
    
    fernet = Fernet(key)
    
    print("\nThis script will encrypt your password so it isn't stored in plain text.")
    password = getpass.getpass("SMTP Password: ")
    
    if not password:
        print("Error: No password provided.")
        sys.exit(1)

    encrypted = fernet.encrypt(password.encode("utf-8"))
    config.paths.secret_password.write_bytes(encrypted)
    config.paths.secret_password.chmod(0o600)
    
    print(f"\n✅ Your password has been encrypted and saved securely inside '{config.paths.secret_password}'.")
    print("You are all set! Now you can edit 'config.yaml' to add receivers and edit your email parameters.")

@task
def check(c):
    """
    Checks for upcoming DST transitions and alerts 1 week and 1 day before.
    """
    check_and_alert()
