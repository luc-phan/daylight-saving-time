from pathlib import Path

import pytest

import dst_notifier.config as config


def write_config(path: Path, notifications: str = "") -> None:
    path.write_text(
        "paths:\n"
        "  secret_key: key\n"
        "  secret_password: password\n"
        "  state_file: state.json\n"
        "smtp:\n"
        "  server: localhost\n"
        "  port: 587\n"
        "  sender_email: sender@example.com\n"
        "receivers:\n"
        "  - recipient@example.com\n"
        "language: french\n"
        f"{notifications}",
        encoding="utf-8",
    )


def test_load_config_parses_configurable_notifications(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.yaml"
    write_config(
        config_path,
        "notifications:\n"
        "  - days_before: 14\n"
        "    template: alert_days_before.txt\n"
        "  - days_before: 7\n"
        "    template: alert_days_before.txt\n",
    )
    monkeypatch.setattr(config, "CONFIG_FILE", config_path)

    loaded = config.load_config()

    assert [(item.days_before, item.template) for item in loaded.notifications] == [
        (14, "alert_days_before.txt"),
        (7, "alert_days_before.txt"),
    ]


def test_load_config_defaults_to_no_notifications_for_existing_configs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.yaml"
    write_config(config_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_path)

    loaded = config.load_config()

    assert loaded.notifications == []


def test_load_config_rejects_duplicate_notification_days(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_path = tmp_path / "config.yaml"
    write_config(
        config_path,
        "notifications:\n"
        "  - days_before: 7\n"
        "    template: alert_days_before.txt\n"
        "  - days_before: 7\n"
        "    template: another_template.txt\n",
    )
    monkeypatch.setattr(config, "CONFIG_FILE", config_path)

    with pytest.raises(SystemExit):
        config.load_config()
