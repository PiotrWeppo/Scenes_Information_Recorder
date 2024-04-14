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

    match len(files_grabbed):
        case 0:
            return
        case 1:
            return files_grabbed[0]
        case other:
            for i, file in enumerate(files_grabbed):
                print("|", i + 1, "|", file)
            choice = input(
                "\nWhich file to open? Choose corresponding number: "
            )
            try:
                os.system("cls||clear")
                print(f"Opening {files_grabbed[int(choice) - 1]}")
                return files_grabbed[int(choice) - 1]
            except IndexError:
                print("\nNumber outside of the list.")
                sys.exit()
            except ValueError:
                print("\nEmpty or wrong input.")
                sys.exit()


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
    dirs = list(dir_paths)
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d)