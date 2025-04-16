import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml


def setup_logging():
    logs_dir = Path("src/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    __location__ = Path(__file__).resolve().parent

    with open(__location__ / "config.yaml") as file:
        config = yaml.safe_load(file)

    logging.config.dictConfig(config["logging"])
