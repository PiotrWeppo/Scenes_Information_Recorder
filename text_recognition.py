import logging
import sys
import cv2
from PIL import Image
import pytesseract
import numpy as np
from tqdm import tqdm

# pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"


def start_logging_errors():
    logging.basicConfig(
        filename="error_log.txt",
        filemode="w",
        format="%(asctime)s %(message)s",
        level=logging.ERROR,
    )


def convert_current_frame_to_tc(frame_number, fps):
    frame_number = int(frame_number)
    fps = int(fps)

    hours = frame_number // (fps * 60 * 60)
    frame_number %= fps * 60 * 60

    minutes = frame_number // (fps * 60)
    frame_number %= fps * 60

    seconds = frame_number // fps
    frames = frame_number % fps

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"


def read_tc_add_one_frame(time_str, video):
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    try:
        hours, minutes, seconds, frames = map(int, time_str.split(":"))
        frames += 1
        if frames == fps:
            frames = 0
            seconds += 1
        if seconds == 60:
            seconds = 0
            minutes += 1
        if minutes == 60:
            minutes = 0
            hours += 1
        cap.release()
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    except ValueError:
        print("Invalid Input")
        input("Press Enter to exit...")
        sys.exit()


# def video_time_length(cap):
#     frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     seconds = frames / fps
#     video_time = datetime.timedelta(seconds=seconds)
#     return video_time


# def set_video_start_time(cap):
#     # seconds = all_frames / fps
#     # frame = seconds * fps
#     # frame = milis / 1000 * fps
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     video_time = video_time_length(cap)
#     end_time = f"0{str(video_time)[3:7]}:{str(video_time)[8:10]}"
#     time_str = input(
#         f"Write time code in the format MM:SS:mm (max time: {end_time}): "
#     )
#     milis = convert_time_to_milliseconds(time_str)
#     start_frame_stamp = milis / 1000 * fps
#     cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_stamp - 1)


def set_video_start_time(video):
    cap = cv2.VideoCapture(video)
    time_code = input(
        "\nPress Enter or set video starting point (Seconds:Frames or StartingFrame): "
    )
    if time_code == "":
        return 0
    if ":" in time_code:
        try:
            seconds, frames = map(int, time_code.split(":"))
            fps = cap.get(cv2.CAP_PROP_FPS)
            start_frame = seconds * fps + frames
        except ValueError:
            print("Invalid Input.")
            input("Press Enter to exit...")
            sys.exit()
    if time_code.isdigit():
        start_frame = int(time_code)
    else:
        print("Invalid Input.")
        input("Press Enter to exit...")
        sys.exit()
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if start_frame > length:
        print("Frame number outside of video length.")
        input("Press Enter to exit...")
        sys.exit()
    cap.release()
    return start_frame


def generate_imgs_with_text_from_video(video, start_frame):
    cap = cv2.VideoCapture(video)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame - 1)
    length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    # print("Position: ", int(cap.get(cv2.CAP_PROP_POS_FRAMES)))
    # Check if camera opened successfully
    # if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) == 0:
    #     print("Current frame: 0")
    # else:
    #     print("Current fram: ", int(cap.get(cv2.CAP_PROP_POS_FRAMES + 1)))
    # # frame_count = 0
    frames_with_embedded_text_id = []
    if cap.isOpened() == False:
        print("Error opening video file")
        input("Press Enter to exit...")
        sys.exit()
    print("\n-Saving frames containing potential text-")
    pbar = tqdm(
        total=length - 1 - start_frame,
        desc="Scanned frames",
        unit="frames",
        leave=True,
    )
    frames_counter = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret == True:
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
            # if current_frame != frame_count:
            #     print("Error frame")
            #     sys.exit(0)
            # print(f"{current_frame}/{length-1}")
            grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(
                grayscale, 230, 255, cv2.THRESH_BINARY_INV
            )
            cropped_img_l = threshold[0:500, 0:1100]
            cropped_img_r = threshold[0:200, 1400:1920]
            n_white_pix = np.sum(cropped_img_l == 0)
            pbar.set_postfix_str(
                f"Frames saved: {frames_counter}", refresh=True
            )
            if n_white_pix >= 500:
                filename = f"frame_{current_frame}.png"
                # print(f"Captured frame: {current_frame}")
                cv2.imwrite("./temp/text_imgs/" + filename, cropped_img_l)
                cv2.imwrite("./temp/tc_imgs/" + filename, cropped_img_r)
                # frames_with_embedded_text_id.append(int(filename.split(".")[0][6:]))
                frames_with_embedded_text_id.append(int(current_frame))
                frames_counter += 1
            # frame_count += 1
            pbar.update(1)

        else:
            break
    # When everything done, release the video capture object
    pbar.close()
    cap.release()

    # Closes all the frames
    cv2.destroyAllWindows()
    return frames_with_embedded_text_id


def check_if_vfx_in_found_scenes(scene_list, frames_with_embedded_text_id):
    each_scene_first_last_frame = [[int(i[0]), int(i[1])] for i in scene_list]
    potential_frames_ranges_with_vfx_text = [
        frame_range
        for frame_range in each_scene_first_last_frame
        if (frame_range[1] - 1) in frames_with_embedded_text_id
    ]
    print(
        f"-Found VFX text in {len(potential_frames_ranges_with_vfx_text)} scenes-"
    )
    return potential_frames_ranges_with_vfx_text


def generate_thumbnails_for_each_scene(
    video, potential_frames_ranges_with_vfx_text
):
    cap = cv2.VideoCapture(video)
    print("\n-Generating Thumbnails-")
    for frame_range in tqdm(
        potential_frames_ranges_with_vfx_text,
        desc="Generated ",
        unit="imgs",
    ):
        begining_frame = frame_range[0]
        cap.set(cv2.CAP_PROP_POS_FRAMES, begining_frame)
        found_frame, frame = cap.read()
        if found_frame:
            img = cv2.resize(frame, None, fx=0.4, fy=0.4)
            cv2.imwrite(f"./temp/thumbnails/{begining_frame}.png", img)
    cap.release()
    cv2.destroyAllWindows()


def generate_vfx_text(
    potential_frames_ranges_with_vfx_text,
    video,
):
    start_logging_errors()
    found_vfx_text = {}
    frames_not_found = []
    print("\n-Reading VFX text-")
    for frame_range in tqdm(
        potential_frames_ranges_with_vfx_text,
        desc="Frames checked",
        unit="frames",
    ):
        first_frame_of_scene = frame_range[0]
        last_frame_of_scene = frame_range[1] - 1
        left_first_image = f"./temp/text_imgs/frame_{first_frame_of_scene}.png"
        right_first_image = f"./temp/tc_imgs/frame_{first_frame_of_scene}.png"
        right_last_image = f"./temp/tc_imgs/frame_{last_frame_of_scene}.png"
        try:
            current_reading_left = [
                list(
                    filter(
                        None,
                        pytesseract.image_to_string(
                            Image.open(left_first_image),
                            lang="eng",
                        ).splitlines(),
                    )
                )
            ]
        except FileNotFoundError as e:
            frames_not_found.append(first_frame_of_scene)
            logging.exception(
                f"Error with frame {first_frame_of_scene}:\n %s", e
            )
            continue
        for text in current_reading_left:
            if text[0].startswith("VFX"):
                current_reading_right = [
                    list(
                        filter(
                            None,
                            pytesseract.image_to_string(
                                Image.open(right_first_image),
                                lang="eng",
                            ).splitlines(),
                        )
                    )
                ]
                last_reading_right = [
                    list(
                        filter(
                            None,
                            pytesseract.image_to_string(
                                Image.open(right_last_image),
                                lang="eng",
                            ).splitlines(),
                        )
                    )
                ]
                tc_out = read_tc_add_one_frame(last_reading_right[0][0], video)
                if first_frame_of_scene not in found_vfx_text:
                    found_vfx_text[first_frame_of_scene] = {}
                    found_vfx_text[first_frame_of_scene]["TEXT"] = text[0]
                    found_vfx_text[first_frame_of_scene]["TC IN"] = (
                        current_reading_right[0][0]
                    )
                    found_vfx_text[first_frame_of_scene]["TC OUT"] = tc_out
                    found_vfx_text[first_frame_of_scene]["FRAME OUT"] = (
                        frame_range[1]
                    )
    print(
        f"Error with frames: {str(frames_not_found)[1:-1]}. Search may be incomplete."
    )
    return found_vfx_text


def generate_adr_text(frames_with_embedded_text_id, video):
    found_adr_text = {}
    print("\n-Searching for ADR text-")
    pbar = tqdm(
        total=len(frames_with_embedded_text_id),
        desc="Frames checked",
        unit="frames",
    )

    for frame in frames_with_embedded_text_id:
        left_image = f"./temp/text_imgs/frame_{frame}.png"
        right_image = f"./temp/tc_imgs/frame_{frame}.png"
        current_reading_left = [
            list(
                filter(
                    None,
                    pytesseract.image_to_string(
                        Image.open(left_image),
                        lang="eng",
                    ).splitlines(),
                )
            )
        ]
        for text in current_reading_left:
            if text[0].startswith("ADR"):
                current_reading_right = [
                    list(
                        filter(
                            None,
                            pytesseract.image_to_string(
                                Image.open(right_image),
                                lang="eng",
                            ).splitlines(),
                        )
                    )
                ]
                pbar.set_postfix_str(
                    f"Last text found: {text[0]}", refresh=True
                )
                if frame not in found_adr_text:
                    found_adr_text[frame] = {}
                    found_adr_text[frame]["TEXT"] = text[0]
                    found_adr_text[frame]["TC"] = current_reading_right[0][0]
        pbar.update(1)
    found_adr_text = remove_all_but_border_cases_found(found_adr_text, video)
    return found_adr_text


def remove_all_but_border_cases_found(text_dict, video):
    numbers = text_dict.keys()
    keys_series = []
    first_and_last_key = []
    new_adr_dict = {}
    for i in numbers:
        # if the keys_series is empty or the element is consecutive
        if (not keys_series) or (keys_series[-1] == i - 1):
            keys_series.append(i)
        else:
            # append a tuple of the first and last item of the keys_series
            first_and_last_key.append((keys_series[0], keys_series[-1]))
            keys_series = [i]
    # needed in case keys_series is empty
    if keys_series:
        first_and_last_key.append((keys_series[0], keys_series[-1]))
    for ranges in first_and_last_key:
        tc_out = read_tc_add_one_frame(text_dict[ranges[1]]["TC"], video)
        new_adr_dict[ranges[0]] = {}
        new_adr_dict[ranges[0]]["TEXT"] = text_dict[ranges[0]]["TEXT"]
        new_adr_dict[ranges[0]]["TC IN"] = text_dict[ranges[0]]["TC"]
        new_adr_dict[ranges[0]]["TC OUT"] = tc_out
        new_adr_dict[ranges[0]]["FRAME OUT"] = ranges[1] + 1
    return new_adr_dict


def merge_dicts(dict_a, dict_b):
    merge_result = {}
    for key in dict_a:
        if key in dict_b:
            merge_result[key] = {
                "text": [dict_a[key]["text"], dict_b[key]["text"]],
                "TC IN": dict_a[key]["TC IN"],
                "TC OUT": [dict_a[key]["TC OUT"], dict_b[key]["TC OUT"]],
            }
        else:
            merge_result[key] = dict_a[key]
    for key in dict_b:
        if key not in dict_a:
            merge_result[key] = dict_b[key]
    sorted_results = dict(sorted(merge_result.items()))
    return sorted_results


def add_real_timestamps(frames_dict, video):
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)

    for frame_number in frames_dict.keys():
        real_tc_in = convert_current_frame_to_tc(frame_number, fps)
        real_tc_out = convert_current_frame_to_tc(
            frames_dict[frame_number]["FRAME OUT"], fps
        )
        frames_dict[frame_number]["REAL TC IN"] = real_tc_in
        frames_dict[frame_number]["REAL TC OUT"] = real_tc_out
    cap.release()
    return frames_dict


if __name__ == "__main__":
    pass
