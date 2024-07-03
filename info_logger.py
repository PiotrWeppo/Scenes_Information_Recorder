"""Module for logging info to a file."""

import logging


def start_logging_info(video_path: str) -> None:
    """Start logging info to a file.

    Args:
        video_path (str): Video path.
    """
    logging.basicConfig(
        filename=f"'{video_path}' info_log.txt",
        filemode="w",
        format="%(asctime)s %(message)s",
        level=logging.DEBUG,
    )
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pyscenedetect").setLevel(logging.WARNING)
