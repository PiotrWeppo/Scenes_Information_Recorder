import glob
import os


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
                return
            except ValueError:
                print("\nEmpty or wrong input.")
                return


def list_of_all_scene_pictures():
    for i in glob.glob("Scene_pictures/*.jpg"):
        print(i)
    return glob.glob("Scene_pictures/*.jpg")