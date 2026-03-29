from __future__ import annotations

import logging

from invoke import Context, task

from dst_notifier.config import load_config
from dst_notifier.utils import init_logging
from dst_notifier.core import check_and_alert, run_setup

logger = logging.getLogger(__name__)


@task
def setup(c: Context) -> None:
    """
    Generates the encryption key, encrypts your SMTP password and saves it locally.
    """
    config = load_config()
    init_logging(config.logging)
    try:
        run_setup(config)
    except Exception:
        logger.exception("setup failed")
        raise


@task
def check(c: Context) -> None:
    """
    Checks for upcoming DST transitions and alerts 1 week and 1 day before.
    """
    config = load_config()
    init_logging(config.logging)
    try:
        check_and_alert(config)
    except Exception:
        logger.exception("check failed")
        raise
