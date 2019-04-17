import os
import sys
import logging.config


DEFAULT_LOG_LEVEL = os.environ.get("LOG_LEVEL", default=logging.DEBUG)


class MaxLevelFilter:
    def __init__(self, max_level=logging.INFO):
        self.max_level = max_level

    def filter(self, record):
        return record.levelno <= self.max_level


def verbosity(v):
    if v == 0:
        return DEFAULT_LOG_LEVEL
    if v == 1:
        return logging.INFO
    if v >= 2:
        return logging.DEBUG


def configure_logger(verbose):
    log_level = verbosity(verbose)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # This section creates the format template for logging messages
            "verbose": {
                "format": "%(asctime)s [%(levelname)s] %(filename)s %(funcName)s %(lineno)d: %(message)s"
            },
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "filters": {
            "max_level_info": {"()": MaxLevelFilter, "max_level": logging.INFO}
        },
        "handlers": {
            # This section creates the locations where log messages will be sent
            "stdout": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "filters": ["max_level_info"],
            },
            "stderr": {
                "level": "WARNING",
                "class": "logging.StreamHandler",
                "stream": sys.stderr,
            },
        },
        "loggers": {
            # This section defines logging objects that will be called out in code
            "rcc": {
                "handlers": ["stdout", "stderr"],
                "propagate": False,
                "level": log_level,
            },
            "": {"handlers": ["stdout", "stderr"], "level": DEFAULT_LOG_LEVEL},
        },
    }

    if verbose == 3:
        config["loggers"][""]["level"] = logging.INFO
    elif verbose >= 4:
        config["loggers"][""]["level"] = logging.DEBUG

    logging.config.dictConfig(config)


configure_logger(0)
