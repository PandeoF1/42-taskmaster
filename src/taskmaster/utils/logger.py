import logging
import os

LOG_FILE = os.path.join("logs", "taskmaster.log")


def _init_logger() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(LOG_FILE)), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


_init_logger()
logger: logging.Logger = logging.getLogger()
