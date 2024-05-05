import logging
import sys
from text_recognition import (
    generate_imgs_with_text_from_video,
    check_if_text_in_found_scenes,
    generate_pictures_for_each_scene,
    n_generate_vfx_text,
    generate_adr_text,
    merge_dicts,
    add_real_timestamps,
    set_video_start_time,
)
from files_operations import (
    find_video_file,
    create_folder,
    delete_folder,
)
from scenes_detection import detect_all_scenes
from xlsx_creator import create_dataframe, create_xlsx_file
from info_logger import start_logging_info


def main():
    print("Welcome to the VFX/ADR text detection program.\n")
    video = find_video_file()
    start_logging_info(video)
    start_frame = set_video_start_time(video)
    create_folder(
        "./temp/text_imgs",
        "./temp/tc_imgs",
        "./temp/thumbnails",
        "./temp/first_last_scene_frames",
    )
    frames_with_embedded_text_id = generate_imgs_with_text_from_video(
        video, start_frame
    )
    logging.debug(
        f"frames_with_embedded_text_id=\n{frames_with_embedded_text_id}\n"
    )
    scene_list = detect_all_scenes(video)
    # loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    # print(loggers)
    logging.debug(f"scene_list=\n{scene_list}\n")
    
    frames_ranges_with_potential_text = check_if_text_in_found_scenes(
        scene_list, frames_with_embedded_text_id
    )
    logging.debug(
        f"frames_ranges_with_potential_text=\n{frames_ranges_with_potential_text}\n"
    )
    # print(frames_with_embedded_text_id)
    generate_pictures_for_each_scene(video, frames_ranges_with_potential_text)
    found_vfx_text = n_generate_vfx_text(
        video, frames_ranges_with_potential_text, frames_with_embedded_text_id
    )
    logging.debug(f"found_vfx_text=\n{found_vfx_text}\n")

    found_adr_text = generate_adr_text(frames_with_embedded_text_id, video)
    logging.debug(f"found_adr_text=\n{found_adr_text}\n")

    merged_text_dict = merge_dicts(found_vfx_text, found_adr_text)
    logging.debug(f"merged_text_dict=\n{merged_text_dict}\n")

    final_text_dict = add_real_timestamps(merged_text_dict, video)
    logging.debug(f"final_text_dict=\n{final_text_dict}\n")

    df = create_dataframe(final_text_dict)
    create_xlsx_file(df, video)
    # delete_folder("./temp")
    input("Done.\n\nPress Enter to exit: ")
    sys.exit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("Main crashed. Error below:\n\n%s", e)
        print("An error occurred. Check the log file for more information.")
        input("Press Enter to exit: ")
        sys.exit()
