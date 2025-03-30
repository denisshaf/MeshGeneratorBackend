import logging.config
from pathlib import Path

import yaml


def setup_logging():
    __location__ = Path(__file__).resolve().parent

    with open(__location__ / "config.yaml") as file:
        config = yaml.safe_load(file)

    logging.config.dictConfig(config['logging'])
