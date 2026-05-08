import logging
import structlog


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure structlog for the application.
    Dev: pretty colored console output.
    Production: swap ConsoleRenderer for JSONRenderer and pipe to a log aggregator.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure stdlib logging so libraries that use it (uvicorn, sqlalchemy)
    # also respect our log level.
    logging.basicConfig(level=level, format="%(message)s")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,  # thread-local context (e.g. run_id)
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),           # swap for JSONRenderer in prod
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
