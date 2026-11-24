import logging

from rich.logging import RichHandler


def setup_logging(verbose: bool = False) -> None:
    """Rich log lines for the ``src`` package: INFO, or DEBUG if verbose.

    Third-party loggers (httpx, qdrant...) stay at WARNING.
    """
    logging.basicConfig(
        level=logging.WARNING,
        format="%(message)s",
        handlers=[RichHandler(show_path=False, show_time=False)],
    )
    logging.getLogger("src").setLevel(
        logging.DEBUG if verbose else logging.INFO
    )
