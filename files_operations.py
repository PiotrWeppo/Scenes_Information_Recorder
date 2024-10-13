"""This module contains functions that perform file operations."""

from typing import List
import sys
import glob
import os
import re
import shutil


def find_video_file() -> List[str]:
    """Find video files in the current directory. Return a list of video files. If no video files are found, exit the program.

    Returns:
        List[str]: List of video files.
    """
    types = ("*.mp4", "*.mov")
    files_grabbed = []
    for files in types:
        files_grabbed.extend(glob.glob(files))
    if len(files_grabbed) == 0:
        print("\nNo video files found.")
        input("Press Enter to exit...")
        sys.exit()
    else:
        return files_grabbed


def list_of_pictures(folder_name: str) -> List[str]:
    """List all the pictures in a folder. Return a list of pictures sorted by their name.

    Args:
        folder_name (str): Folder name.

    Returns:
        List[str]: List of pictures sorted by their name.
    """
    files = glob.glob(os.path.join(folder_name, "*.png"))
    files.sort(
        key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", x)]
    )
    return files


def create_folder(*dir_paths: str) -> None:
    """Create temporary folders.

    Args:
        *dir_paths (str): Folder names.
    """
    print("\n-Creating temporary folders-")
    dirs = list(dir_paths)
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)


def delete_folder(*dir_paths: str) -> None:
    """Delete temporary folders.

    Args:
        *dir_paths (str): Folder names.
    """
    print("\n-Deleting temporary folders-")
    dirs = list(dir_paths)
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        else:
            print(f"The folder {d} does not exist.")


def copy_picture_from_to_folder(source_path: str, destination_path: str) -> None:
    """Copy a picture from one folder to another.

    Args:
        source_path (str): Source path.
        destination_path (str): Destination path.
    """
    shutil.copy(source_path, destination_path)


def delete_temp_folder_on_error_and_exit(
    dir_path: str, optional_print: str = None
) -> None:
    """Delete temporary folders on error and exit the program.

    Args:
        optional_print (str, optional): Optional message to print. Defaults to None.
    """
    if optional_print:
        print(optional_print)
    choice = input(
        "\nAn error occurred. Check log file. Delete temporary files before closing? (y/n): "
    )
    if choice.lower() in ["y", "yes", ""]:
        delete_folder(f"{dir_path}/temp")
        print("\nTemporary files deleted.")
    input("No files deleted. Press Enter to exit: ")
    sys.exit()
