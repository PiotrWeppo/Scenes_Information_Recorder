#!/usr/bin/env python3
# *_* coding: utf-8 *_*
"""This module deploys VFX/ADR text detection program."""

import logging
import sys
from gui import AppGui
from text_recognition import TextRecognition
from files_operations import (
    find_video_file,
    create_folder,
    delete_folder,
    delete_temp_folder_on_error_and_exit,
)
from scenes_detection import detect_all_scenes
from xlsx_creator import create_dataframe, create_xlsx_file
from info_logger import start_logging_info


def main() -> None:
    """Main function of the program."""
    print("Welcome to the VFX/ADR text detection program.\n")
    gui = AppGui()
    video_names = find_video_file()
    gui.create_main_screen(video_names)
    video = gui.video_name
    start_logging_info(video)
    if gui.scale_value is not None:
        start_time = gui.scale_value.get()
    else:
        start_time = 0
    text_area = gui.text_area
    tc_area = gui.tc_area
    print(f"start_time={start_time}")
    print(f"text_area={text_area}")
    print(f"tc_area={tc_area}")
    create_folder(
        "./temp/text_imgs",
        "./temp/tc_imgs",
        "./temp/thumbnails",
        "./temp/first_last_scene_frames",
    )
    text_recognition = TextRecognition(
        gui.cap, video, start_time, text_area, tc_area
    )
    frames_with_embedded_text_id = (
        text_recognition.generate_imgs_with_text_from_video()
    )
    logging.debug(
        f"frames_with_embedded_text_id=\n{frames_with_embedded_text_id}\n"
    )
    scene_list = detect_all_scenes(video)
    # loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    # print(loggers)
    logging.debug(f"scene_list=\n{scene_list}\n")

    frames_ranges_with_potential_text = (
        text_recognition.check_if_vfx_text_in_found_scenes(
            scene_list, frames_with_embedded_text_id
        )
    )
    logging.debug(
        f"frames_ranges_with_potential_text=\n{frames_ranges_with_potential_text}\n"
    )
    # print(frames_with_embedded_text_id)
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
    create_xlsx_file(df, video)
    delete_folder("./temp")
    input("Done.\n\nPress Enter to exit: ")
    sys.exit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Main crashed. Error below:\n\n%s", e)
        delete_temp_folder_on_error_and_exit("Main crashed.")
