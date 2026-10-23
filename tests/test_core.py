from datetime import date
from pathlib import Path

import dst_notifier.core as core
from dst_notifier.config import AppConfig, PathsConfig, SmtpConfig
from dst_notifier.core import get_last_sunday, get_dst_transitions

def test_get_last_sunday():
    # 2024: March 31 was Sunday
    assert get_last_sunday(2024, 3) == date(2024, 3, 31)
    # 2024: Oct 27 was Sunday
    assert get_last_sunday(2024, 10) == date(2024, 10, 27)
    
    # 2025: March 30 is Sunday
    assert get_last_sunday(2025, 3) == date(2025, 3, 30)

def test_get_dst_transitions():
    transitions = get_dst_transitions(2026)
    assert len(transitions) == 2
    
    # 2026: March 29 is Sunday
    assert transitions[0][0] == date(2026, 3, 29)
    assert "Summer Time" in transitions[0][1]
    
    # 2026: Oct 25 is Sunday
    assert transitions[1][0] == date(2026, 10, 25)
    assert "Winter Time" in transitions[1][1]


def test_check_and_alert_logs_countdown_on_every_check(
    tmp_path: Path, monkeypatch, caplog
) -> None:
    import logging

    current_day = [date(2026, 3, 22)]

    class FixedDate(date):
        @classmethod
        def today(cls) -> date:
            return current_day[0]

    template_dir = tmp_path / "templates" / "french"
    template_dir.mkdir(parents=True)
    (template_dir / "alert_7_days.txt").write_text(
        "{% block subject %}Reminder in {{ diff_days }} days{% endblock %}"
        "{% block body %}{{ label }}{% endblock %}",
        encoding="utf-8",
    )
    config = AppConfig(
        paths=PathsConfig(
            secret_key=tmp_path / "key",
            secret_password=tmp_path / "password",
            state_file=tmp_path / "state.json",
        ),
        smtp=SmtpConfig(server="localhost", port=25, sender_email="sender@example.com"),
        receivers=["recipient@example.com"],
        language="french",
        logging=None,
    )
    sent: list[tuple[str, str]] = []

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(core, "date", FixedDate)
    monkeypatch.setattr(
        core,
        "get_dst_transitions",
        lambda year: [(date(2026, 3, 29), "Summer Time (+1h, sleep less!)")],
    )
    monkeypatch.setattr(
        core,
        "send_alert_emails",
        lambda subject, body, config: sent.append((subject, body)),
    )

    core.check_and_alert(config)

    assert sent == [
        ("Reminder in 7 days", "Summer Time (+1h, sleep less!)")
    ]

    current_day[0] = date(2026, 3, 27)
    caplog.set_level(logging.INFO, logger="dst_notifier.core")
    caplog.clear()

    core.check_and_alert(config)

    assert "Time change (Summer Time (+1h, sleep less!)) is in 2 days" in caplog.text
    assert len(sent) == 1
