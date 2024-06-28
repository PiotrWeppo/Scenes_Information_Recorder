import sys
import glob
import os
import re
import shutil


def find_video_file():
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


# def list_of_all_scene_pictures(folder_name):
#     return sorted(glob.glob(f"{folder_name}/*.png"))


def list_of_pictures(folder_name):
    files = glob.glob(os.path.join(folder_name, "*.png"))
    files.sort(
        key=lambda x: [
            int(c) if c.isdigit() else c for c in re.split(r"(\d+)", x)
        ]
    )
    return files


def create_folder(*dir_paths):
    print("\n-Creating temporary folders-")
    dirs = list(dir_paths)
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)


def delete_folder(*dir_paths):
    print("\n-Deleting temporary folders-")
    dirs = list(dir_paths)
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        else:
            print(f"The folder {d} does not exist.")


def copy_picture_from_to_folder(source_path, destination_path):
    shutil.copy(source_path, destination_path)


def delete_temp_folder_on_error_and_exit(optional_print=None):
    if optional_print:
        print(optional_print)
    choice = input(
        "\nAn error occurred. Check log file. Delete temporary files before closing? (y/n): "
    )
    if choice.lower() in ["y", "yes", ""]:
        delete_folder("./temp")
        print("\nTemporary files deleted.")
    input("Press Enter to exit: ")
    sys.exit()
