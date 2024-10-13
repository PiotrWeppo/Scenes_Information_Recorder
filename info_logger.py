"""Module for logging info to a file."""

import os
import logging


def start_logging_info(video_path: str, log_dir: str) -> None:
    """Start logging info to a file.

    Args:
        video_path (str): Video path.
    """

    file_name = os.path.basename(video_path).split("/")[-1]
    log_file_path = os.path.join(log_dir, f"'{file_name}' info_log.txt")
    logging.basicConfig(
        filename=log_file_path,
        filemode="w",
        format="%(asctime)s %(message)s",
        level=logging.DEBUG,
    )
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pyscenedetect").setLevel(logging.WARNING)
    logging.getLogger("pytesseract").setLevel(logging.WARNING)


def delete_logging_file(video_path: str, log_dir: str) -> None:
    """Delete the specific logging file created by start_logging_info.

    Args:
        video_path (str): Video path.
        log_dir (str): Log directory.
    """
    file_name = os.path.basename(video_path).split("/")[-1]
    log_file_path = os.path.join(log_dir, f"'{file_name}' info_log.txt")
    
    logger = logging.getLogger()
    handlers = logger.handlers[:]
    for handler in handlers:
        handler.close()
        logger.removeHandler(handler)
    
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    else:
        print(f"{log_file_path} does not exist.")
