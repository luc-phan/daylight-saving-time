# daylight-saving-time

Small Python notifier that sends email reminders before daylight saving time (DST)
changes using European rules:

- Last Sunday of March: summer time starts.
- Last Sunday of October: winter time starts.

The app can send reminders:

- on configurable days before the transition

It uses:

- `PyYAML` for config loading
- `Jinja2` templates for email subject/body
- `cryptography` (`Fernet`) to store SMTP password encrypted at rest
- `invoke` tasks for setup and execution

## Project structure

- `dst_notifier/` - core logic (`config.py`, `core.py`)
- `etc/config.example.yaml` - example config
- `etc/config.yaml` - your local config (create from the example)
- `templates/french/` - email templates
- `templates.example/french/` - starter templates you can copy/customize
- `var/` - runtime files (encrypted secret, state, logs)
- `tasks.py` - `invoke` entrypoints
- `tests/` - unit tests

## Requirements

- Python 3.10+
- `uv`
- Access to an SMTP server

## Usage

For runtime usage only (no test/dev tooling), install app dependencies and create
your config:

```bash
uv sync
mkdir -p var
cp etc/config.example.yaml etc/config.yaml
cp -r templates.example templates
```

## Configuration

Edit `etc/config.yaml`:

- `paths.secret_key`: where encryption key is stored
- `paths.secret_password`: where encrypted SMTP password is stored
- `paths.state_file`: where sent-alert state is stored
- `smtp.server`, `smtp.port`, `smtp.sender_email`
- `receivers`: list of destination emails
- `language`: template language folder name (currently `french`)
- `notifications`: list of reminders, each with `days_before` and `template`.
  For example:

  ```yaml
  notifications:
    - days_before: 14
      template: alert_days_before.txt
    - days_before: 7
      template: alert_days_before.txt
    - days_before: 1
      template: alert_1_day.txt
    - days_before: 0
      template: alert_0_day.txt
  ```

  A reminder is sent once its configured day is reached. If checks were missed,
  only the most recent overdue reminder is sent; earlier missed reminders are
  skipped. The state file records the last notification date per transition,
  independently of the configured reminder days. If omitted, notifications
  default to the legacy 7-day, 1-day, and transition-day reminders.

  For example, after a notification for the October 25 transition on October
  23, the state contains:

  ```json
  {
    "2026-10-25": {
      "last_notification": "2026-10-23"
    }
  }
  ```

- `logging`: optional Python logging config

## First-time setup

Run the setup task to generate a local encryption key and save the encrypted SMTP
password:

```bash
uv run inv setup
```

This creates (by default):

- `var/.secret_key`
- `var/.secret_password`

Both files are created with restricted permissions (`0600`).

## Run a check manually

```bash
uv run inv check
```

The command:

- computes upcoming DST transitions for the current year
- checks whether a reminder should be sent today
- skips reminders already sent (state tracked in `var/state.json`)
- renders the correct template and sends email through SMTP

## Email templates

Templates live in `templates/<language>/` and define two Jinja blocks:

- `subject`
- `body`

Current files:

- `alert_days_before.txt`
- `alert_1_day.txt`
- `alert_0_day.txt`

`alert_days_before.txt` is suitable for any multi-day reminder because its
content uses the `diff_days` template variable. Older configurations that omit
`notifications` continue to use `alert_7_days.txt` for the 7-day reminder.
For an existing installation using the new configurable example, copy
`templates.example/french/alert_days_before.txt` into
`templates/french/alert_days_before.txt`.

## Scheduling (recommended)

Run `uv run inv check` daily with cron/systemd so reminders are sent automatically.

Example cron entry (runs every day at 11:00):

```cron
0 11 * * * cd /path/to/daylight-saving-time && uv run inv check >> /path/to/daylight-saving-time/var/debug_cron.log 2>&1
```

## Development

Install development dependencies (including test tools):

```bash
uv sync --dev
```

Run tests:

```bash
uv run pytest
```

Quick commands:

```bash
uv run inv setup   # initialize local secrets
uv run inv check   # run DST check now
uv run pytest      # run tests
```

### Cheat sheet

#### Module not found

```bash
$ uv run pytest
...
E   ModuleNotFoundError: No module named 'dst_notifier'
```

```bash
$ vim pyproject.toml
```

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
```

Or:

```bash
touch tests/__init__.py
```

### TODO

- ~~Add typing~~
- ~~Add directories:~~
  - ~~etc/~~
  - ~~var/~~
