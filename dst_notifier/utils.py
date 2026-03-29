from __future__ import annotations

import logging
import logging.config
from typing import Any


def init_logging(cfg: dict[str, Any] | None) -> None:
    """Apply ``logging.config.dictConfig`` from YAML, or a minimal default if absent."""
    if cfg is None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return
    logging.config.dictConfig(cfg)
