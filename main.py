#!/usr/bin/env python3
# *_* coding: utf-8 *_*
"""This module deploys VFX/ADR text detection program."""

import logging
import sys

# from gui import AppGui
from PySide6.QtWidgets import QApplication
from pyside_gui import MainWindow
from text_recognition import TextRecognition
from files_operations import (
    create_folder,
    delete_folder,
    delete_temp_folder_on_error_and_exit,
)
from scenes_detection import detect_all_scenes
from xlsx_creator import create_dataframe, create_xlsx_file
from info_logger import start_logging_info, delete_logging_file


class DataHandler:
    def __init__(self):
        self.received_data = None

    def handle_data(self, data):
        self.received_data = data


def main() -> None:
    """Main function of the program."""

    print("\nWelcome to the VFX/ADR text detection program.\n")
    # gui = AppGui()
    app = QApplication()
    app.setStyle("Fusion")
    data_handler = DataHandler()
    window = MainWindow(app)
    window.data_signal.connect(
        data_handler.handle_data
    )  # Connect the signal to the slot
    window.show()
    app.exec()
    gui_data = data_handler.received_data
    if gui_data is None or len(gui_data) < 5:
        print("App closed before processing. Goodbye.")
        sys.exit()
    video = gui_data["video_path"]
    files_path = gui_data["files_save_dir"]
    text_area = gui_data["text_areas"]["VFX/ADR"]
    tc_area = gui_data["text_areas"]["TC"]
    cv2_cap_obj = gui_data["cv2_cap_obj"]
    save_hq_pics = gui_data["save_hq_pics"]
    start_logging_info(video, files_path)
    if gui_data["start_frame"] is not None:
        start_time = gui_data["start_frame"]
    else:
        start_time = 0
    create_folder(
        f"{files_path}/temp/text_imgs",
        f"{files_path}/temp/tc_imgs",
        f"{files_path}/temp/thumbnails",
        f"{files_path}/temp/first_last_scene_frames",
    )
    text_recognition = TextRecognition(
        cv2_cap_obj, files_path, video, start_time, text_area, tc_area
    )
    frames_with_embedded_text_id = (
        text_recognition.generate_imgs_with_text_from_video()
    )
    logging.debug(
        f"frames_with_embedded_text_id=\n{frames_with_embedded_text_id}\n"
    )
    scene_list = detect_all_scenes(video)
    print("finished scene list")
    logging.debug(f"scene_list=\n{scene_list}\n")
    frames_ranges_with_potential_text = (
        text_recognition.check_if_scenes_can_contain_text(
            scene_list, frames_with_embedded_text_id
        )
    )
    logging.debug(
        f"frames_ranges_with_potential_text=\n{frames_ranges_with_potential_text}\n"
    )
    text_recognition.generate_pictures_for_each_scene(
        frames_ranges_with_potential_text
    )
    found_vfx_text = text_recognition.generate_vfx_text(
        frames_ranges_with_potential_text, frames_with_embedded_text_id
    )
    logging.debug(f"found_vfx_text=\n{found_vfx_text}\n")

    found_adr_text = text_recognition.generate_adr_text(
        frames_with_embedded_text_id
    )
    logging.debug(f"found_adr_text=\n{found_adr_text}\n")

    merged_text_dict = text_recognition.merge_dicts(
        found_vfx_text, found_adr_text
    )
    logging.debug(f"merged_text_dict=\n{merged_text_dict}\n")

    final_text_dict = text_recognition.add_real_timestamps(merged_text_dict)
    logging.debug(f"final_text_dict=\n{final_text_dict}\n")

    df = create_dataframe(final_text_dict)
    create_xlsx_file(df, video, files_path, save_hq_pics)
    delete_folder(f"{files_path}/temp")
    delete_logging_file(video, files_path)

    input("Done.\n\nPress Enter to exit: ")
    sys.exit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Main crashed. Error below:\n\n%s", e)
        # delete_temp_folder_on_error_and_exit("Main crashed.")
