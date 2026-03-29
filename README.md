# daylight-saving-time

Small Python notifier that sends email reminders before daylight saving time (DST)
changes using European rules:

- Last Sunday of March: summer time starts.
- Last Sunday of October: winter time starts.

The app can send alerts:

- 7 days before
- 1 day before
- the day of the transition

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

- `alert_7_day.txt`
- `alert_1_day.txt`
- `alert_0_day.txt`

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

- Add typing
- ~~Add directories:~~
  - ~~etc/~~
  - ~~var/~~
- ~~Finish the readme file~~
