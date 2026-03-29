import smtplib
from datetime import date, timedelta
from email.message import EmailMessage
from email.utils import formatdate
import logging
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

def load_state(state_file: Path) -> dict:
    if state_file.exists():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}

def save_state(state: dict, state_file: Path):
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

logger = logging.getLogger(__name__)

from dst_notifier.config import load_config, decrypt_password

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

def send_alert_emails(subject: str, body: str, config):
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

def check_and_alert():
    """Main check function. Separate from Invoke task so it can be tested theoretically."""
    config = load_config()
    today = date.today()
    transitions = get_dst_transitions(today.year)
    
    logger.info(f"Today's date: {today.strftime('%d/%m/%Y')}")
    alert_triggered = False
    state = load_state(config.paths.state_file)
    env = Environment(loader=FileSystemLoader('.'))
    
    for transition_date, label in transitions:
        diff_days = (transition_date - today).days
        
        if diff_days < 0:
            continue
            
        alert_0_key = f"{transition_date.isoformat()}_T0"
        alert_1_key = f"{transition_date.isoformat()}_T1"
        alert_7_key = f"{transition_date.isoformat()}_T7"
        
        if diff_days == 0:
            if alert_0_key not in state:
                logger.warning(f"ALERT: Time change ({label}) is TODAY!")

                template = env.get_template(f'templates/{config.language}/alert_0_day.txt')
                context = dict(label=label)
                t_render = template.new_context(context)
                subject = "".join(template.blocks['subject'](t_render))
                body = "".join(template.blocks['body'](t_render))

                send_alert_emails(
                    subject=subject,
                    body=body,
                    config=config
                )
                state[alert_0_key] = True
                alert_triggered = True
        elif 0 <= diff_days <= 1:
            if alert_1_key not in state:
                logger.warning(f"ALERT: Time change ({label}) is TOMORROW!")
                send_alert_emails(
                    subject=f"🕒 Final reminder: Time change TOMORROW ({label})",
                    body=f"Don't get caught off guard! The time change ({label}) is tonight! It will be {transition_date.strftime('%d/%m/%Y')}.",
                    config=config
                )
                state[alert_1_key] = True
                alert_triggered = True
                
            if alert_7_key not in state:
                state[alert_7_key] = True
                
        elif 1 < diff_days <= 7:
            if alert_7_key not in state:
                logger.warning(f"ALERT: Time change ({label}) in {diff_days} days.")
                send_alert_emails(
                    subject=f"🕒 Alert T-7: Time change ({label})",
                    body=f"Get ready! The time change ({label}) will happen in {diff_days} days, on {transition_date.strftime('%d/%m/%Y')}.",
                    config=config
                )
                state[alert_7_key] = True
                alert_triggered = True
                
        elif diff_days > 7:
            logger.info(f"Time change ({label}) is in {diff_days} days (on {transition_date.strftime('%d/%m/%Y')}).")
            
    save_state(state, config.paths.state_file)
        
    if not alert_triggered:
        logger.info("No alert to send today.")
