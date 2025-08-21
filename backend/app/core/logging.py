from logging.config import dictConfig

from .config import settings


def setup_logging():
    """Setup comprehensive logging for the platform using dictConfig"""
    log_dir = settings.logs_dir

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s | %(message)s"
            },
            "simple": {"format": "%(asctime)s | %(levelname)-8s | %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_dir / "data_quality_platform.log"),
            },
            "agent_file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "agent_activities.log"),
            },
        },
        "loggers": {
            "": {"level": "INFO", "handlers": ["console", "file"]},
            "agents": {"level": "INFO", "handlers": ["agent_file"], "propagate": False},
        },
    }

    dictConfig(logging_config)
