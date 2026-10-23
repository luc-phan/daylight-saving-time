from __future__ import annotations

import getpass
import json
import logging
import smtplib
from datetime import date, timedelta
from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from jinja2 import Environment, FileSystemLoader

from dst_notifier.config import AppConfig, decrypt_password

def load_state(state_file: Path) -> dict[str, Any]:
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}

def save_state(state: dict[str, Any], state_file: Path) -> None:
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

logger = logging.getLogger(__name__)


def run_setup(config: AppConfig) -> None:
    """Create encryption key and encrypted SMTP password (``load_config`` + ``init_logging`` in the entrypoint)."""
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
        raise ValueError("No password provided.")

    encrypted = fernet.encrypt(password.encode("utf-8"))
    config.paths.secret_password.write_bytes(encrypted)
    config.paths.secret_password.chmod(0o600)

    print(
        f"\n✅ Your password has been encrypted and saved securely inside "
        f"'{config.paths.secret_password}'."
    )
    print(
        "You are all set! Now you can edit 'config.yaml' to add receivers and "
        "edit your email parameters."
    )


def get_last_sunday(year: int, month: int) -> date:
    """Calculates the last Sunday of a given month."""
    if month == 12:
        last_day = date(year, 12, 31)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    offset = last_day.isoweekday() % 7
    return last_day - timedelta(days=offset)

def get_dst_transitions(year: int) -> list[tuple[date, str]]:
    """Calculates European DST transition rules."""
    return [
        (get_last_sunday(year, 3), "Summer Time (+1h, sleep less!)"),
        (get_last_sunday(year, 10), "Winter Time (-1h, sleep more!)")
    ]

def send_alert_emails(subject: str, body: str, config: AppConfig) -> None:
    """Sends the email to all receivers configured in config.yaml using smtplib."""
    password = decrypt_password(config)
    
    if not config.receivers:
        logger.warning("No receivers configured in config.yaml. Skipping email.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = config.smtp.sender_email
    msg["To"] = ", ".join(config.receivers)
    msg["Date"] = formatdate(localtime=True)
    
    logger.info(f"Connecting to SMTP server {config.smtp.server}...")
    with smtplib.SMTP(config.smtp.server, config.smtp.port) as server:
        server.starttls()
        server.login(config.smtp.sender_email, password)
        server.send_message(msg)
        logger.info(f"Email successfully sent to {len(config.receivers)} recipients!")

def check_and_alert(config: AppConfig) -> None:
    """DST transition check and alerts (call ``load_config()`` first)."""
    today = date.today()
    transitions = get_dst_transitions(today.year)

    logger.info(f"Today's date: {today.strftime('%d/%m/%Y')}")
    alert_triggered = False
    state = load_state(config.paths.state_file)
    env = Environment(loader=FileSystemLoader("."))

    for transition_date, label in transitions:
        diff_days = (transition_date - today).days
        
        if diff_days < 0:
            continue

        logger.info(f"Time change ({label}) is in {diff_days} days (on {transition_date.strftime('%d/%m/%Y')}).")
            
        alert_0_key = f"{transition_date.isoformat()}_T0"
        alert_1_key = f"{transition_date.isoformat()}_T1"
        alert_7_key = f"{transition_date.isoformat()}_T7"
        
        if diff_days == 0:
            # if not state.get(alert_0_key):
            #     logger.warning(f"ALERT: Time change ({label}) is TODAY!")

            #     template = env.get_template(f'templates/{config.language}/alert_0_day.txt')
            #     context = dict(label=label)
            #     t_render = template.new_context(context)
            #     subject = "".join(template.blocks['subject'](t_render))
            #     body = "".join(template.blocks['body'](t_render))

            #     send_alert_emails(
            #         subject=subject,
            #         body=body,
            #         config=config
            #     )
            #     state[alert_0_key] = True
            #     alert_triggered = True

            notified = notify(state, alert_0_key, env, config, label, diff_days, 'alert_0_day.txt')

            if notified:
                state[alert_0_key] = True
                alert_triggered = True

        elif diff_days == 1:
            # if not state.get(alert_1_key):
            #     logger.warning(f"ALERT: Time change ({label}) is TOMORROW!")

            #     template = env.get_template(f'templates/{config.language}/alert_1_day.txt')
            #     context = dict(label=label)
            #     t_render = template.new_context(context)
            #     subject = "".join(template.blocks['subject'](t_render))
            #     body = "".join(template.blocks['body'](t_render))

            #     send_alert_emails(
            #         subject=subject,
            #         body=body,
            #         config=config
            #     )
            #     state[alert_1_key] = True
            #     alert_triggered = True

            notified = notify(state, alert_1_key, env, config, label, diff_days, 'alert_1_day.txt')

            if notified:
                state[alert_1_key] = True
                alert_triggered = True

        elif 2 < diff_days <= 7:
            # if not state.get(alert_7_key):
            #     logger.warning(f"ALERT: Time change ({label}) in {diff_days} days.")

            #     template = env.get_template(f'templates/{config.language}/alert_7_days.txt')
            #     context = dict(label=label, diff_days=diff_days)
            #     t_render = template.new_context(context)
            #     subject = "".join(template.blocks['subject'](t_render))
            #     body = "".join(template.blocks['body'](t_render))

            #     send_alert_emails(
            #         subject=subject,
            #         body=body,
            #         config=config
            #     )
            #     state[alert_7_key] = True
            #     alert_triggered = True
            
            notified = notify(state, alert_7_key, env, config, label, diff_days, 'alert_7_days.txt')

            if notified:
                state[alert_7_key] = True
                alert_triggered = True

    save_state(state, config.paths.state_file)

    if not alert_triggered:
        logger.info("No alert to send today.")

def notify(
    state: dict[str, Any],
    key: str,
    env: Environment,
    config: AppConfig,
    label: str,
    diff_days: int,
    template_name: str,
) -> bool:
    if not state.get(key):
        logger.warning(f"ALERT: Time change ({label}) in {diff_days} days.")

        template = env.get_template(f'templates/{config.language}/{template_name}')
        context = dict(label=label, diff_days=diff_days)
        t_render = template.new_context(context)
        subject = "".join(template.blocks['subject'](t_render))
        body = "".join(template.blocks['body'](t_render))

        send_alert_emails(
            subject=subject,
            body=body,
            config=config
        )

        # state[alert_7_key] = True
        # alert_triggered = True
        return True
    return False
