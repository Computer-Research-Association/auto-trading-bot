import logging
import logging.handlers
import sys


def setup_logging() -> None:
    stream_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(getattr(logging, "INFO", logging.INFO))

    if not root.handlers:
        root.addHandler(stream_handler)

logger = logging.getLogger("api-server")
