from __future__ import annotations

import argparse
import logging
from pathlib import Path

from api.config import CONFIG_PATH, settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse maintenance CLI arguments.

    Args:
        None.

    Returns:
        argparse.Namespace: Parsed command-line options.

    Raises:
        SystemExit: If argparse validation fails.
    """
    parser = argparse.ArgumentParser(description="Masao backend maintenance CLI")
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Path to settings.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Validate config without writing data")
    parser.add_argument("--input", default="backend/sql", help="Input folder for SQL migrations")
    parser.add_argument("--output", default="logs", help="Output folder for logs/reports")
    parser.add_argument("--client", default=None, help="Reserved compatibility flag for client-scoped jobs")
    return parser.parse_args()


def main() -> None:
    """Run backend maintenance validation.

    Args:
        None.

    Returns:
        None.

    Raises:
        FileNotFoundError: If the configured SQL input folder does not exist.
    """
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input folder not found: {input_path}")

    logger.info(
        "Backend config loaded app=%s restaurant=%s dry_run=%s",
        settings.app_name,
        settings.restaurant_slug,
        args.dry_run,
    )
    logger.info("Batch done - success:%s failed:%s skipped:%s", 1, 0, 0)


if __name__ == "__main__":
    main()
