import logging
import re
import cv2
from PIL import Image
import pytesseract
import numpy as np
from tqdm import tqdm

from files_operations import delete_temp_folder_on_error_and_exit


class TextRecognition:
    def __init__(self, cap, video, time_code, text_area, tc_area):
        self.cap = cap
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.video_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video = video
        self.time_code = time_code
        self.set_video_start_time()
        self.text_area = text_area
        self.tc_area = tc_area

    def convert_current_frame_to_tc(self, frame_number):
        frame_number = int(frame_number)
        fps = int(self.video_fps)

        hours = frame_number // (fps * 60 * 60)
        frame_number %= fps * 60 * 60

        minutes = frame_number // (fps * 60)
        frame_number %= fps * 60

        seconds = frame_number // fps
        frames = frame_number % fps

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    def read_tc_add_one_frame(self, time_str):
        hours, minutes, seconds, frames = map(int, time_str.split(":"))
        frames += 1
        if frames == self.video_fps:
            frames = 0
            seconds += 1
        if seconds == 60:
            seconds = 0
            minutes += 1
        if minutes == 60:
            minutes = 0
            hours += 1
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    def set_video_start_time(self):
        # TODO Connect to the gui, make case for SS:FF code
        time_code = str(self.time_code)
        if time_code == "":
            return 0
        if time_code.isdigit():
            start_frame = int(time_code)
        elif ":" in time_code:
            try:
                seconds, frames = map(int, time_code.split(":"))
                start_frame = int(seconds * self.video_fps + frames)
            except ValueError:
                delete_temp_folder_on_error_and_exit("Invalid Input.")
        else:
            delete_temp_folder_on_error_and_exit("Invalid Input.")
        if start_frame > self.video_length:
            delete_temp_folder_on_error_and_exit(
                "Frame number outside of video length."
            )
        self.start_frame = start_frame

    def tc_cleanup_from_potential_errors(self, tc_text, frame_number):
        if not tc_text or not tc_text[0]:
            return "EMPTY TC"
        pattern = re.compile(r"(\d{2})")
        joined_text = "".join(tc_text[0])
        try:
            x = re.findall(pattern, joined_text)
            formated_text = f"{x[0]}:{x[1]}:{x[2]}:{x[3]}"
        except IndexError as e:
            logging.exception(
                f"Error with frame {frame_number}. Trying to format and clean TC: '{joined_text}'.\n%s",
                e,
            )
            return "WRONG TC"
        return formated_text

    def match_text(self, text, beginning_chars):
        pattern = re.compile(beginning_chars + r"\s*(.+)", re.IGNORECASE)
        match = re.search(pattern, text)
        if match is None:
            return None
        else:
            return match.group()

    def evenly_spaced_nums_from_range(
        self, range_list, q_nums=3, endpoint=True, nums_with_borders=True
    ):
        generated_numbers = np.linspace(
            range_list[0],
            range_list[1],
            num=q_nums,
            endpoint=endpoint,
            dtype=int,
        )
        if not nums_with_borders:
            numbers_from_center = generated_numbers[1:-1].tolist()
            return numbers_from_center
        return generated_numbers.tolist()

    def generate_imgs_with_text_from_video(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        frames_with_embedded_text_id = []
        if self.cap.isOpened() == False:
            delete_temp_folder_on_error_and_exit("Error opening video file")
        print("\n-Saving frames containing potential text-")
        pbar = tqdm(
            total=self.video_length - 1 - self.start_frame,
            desc="Scanned frames",
            unit="frames",
            leave=True,
        )
        frames_counter = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret == True:
                current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
                grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                _, threshold = cv2.threshold(
                    grayscale, 245, 255, cv2.THRESH_BINARY_INV
                )
                top_left, _, bottom_right, _ = self.text_area
                cropped_img_l = threshold[
                    top_left[1] : bottom_right[1],
                    top_left[0] : bottom_right[0],
                ]
                top_left, _, bottom_right, _ = self.tc_area
                cropped_img_r = threshold[
                    top_left[1] : bottom_right[1],
                    top_left[0] : bottom_right[0],
                ]
                n_white_pix = np.sum(cropped_img_l == 0)
                pbar.set_postfix_str(
                    f"Frames saved: {frames_counter}", refresh=True
                )
                if n_white_pix >= 500:
                    filename = f"frame_{current_frame}.png"
                    cv2.imwrite("./temp/text_imgs/" + filename, cropped_img_l)
                    cv2.imwrite("./temp/tc_imgs/" + filename, cropped_img_r)
                    # frames_with_embedded_text_id.append(int(filename.split(".")[0][6:]))
                    frames_with_embedded_text_id.append(int(current_frame))
                    frames_counter += 1
                pbar.update(1)
            else:
                break
        pbar.close()

        return frames_with_embedded_text_id

    def check_if_vfx_text_in_found_scenes(
        self, scene_list, frames_with_embedded_text_id
    ):
        each_scene_first_last_frame = [
            [int(i[0]), int(i[1])] for i in scene_list
        ]
        numbers_to_check = [
            self.evenly_spaced_nums_from_range(range, q_nums=5, endpoint=False)
            for range in each_scene_first_last_frame
        ]
        # potential_frames_ranges_with_vfx_text = [
        #     frame_range
        #     for frame_range in each_scene_first_last_frame
        #     if any(
        #         frame in frames_with_embedded_text_id
        #         for frame in range(frame_range[0], frame_range[1])
        #     )
        # ]
        potential_frames_ranges_with_vfx_text = []
        for sublist in numbers_to_check:
            if any(frame in frames_with_embedded_text_id for frame in sublist):
                potential_frames_ranges_with_vfx_text.append(
                    [
                        each_scene_first_last_frame[
                            numbers_to_check.index(sublist)
                        ][0],
                        each_scene_first_last_frame[
                            numbers_to_check.index(sublist)
                        ][1],
                    ]
                )
        print(
            f"-Found potential text in {len(potential_frames_ranges_with_vfx_text)} scenes-"
        )
        return potential_frames_ranges_with_vfx_text

    def generate_pictures_for_each_scene(
        self, potential_frames_ranges_with_vfx_text
    ):

        print("\n-Generating Pictures-")
        for frame_range in tqdm(
            potential_frames_ranges_with_vfx_text,
            desc="Generated ",
            unit="imgs",
        ):
            begining_frame = frame_range[0]
            last_frame = frame_range[1] - 1
            which_frame_from_loop = 0
            for frame_number in [begining_frame, last_frame]:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                found_frame, frame = self.cap.read()
                if found_frame:
                    if which_frame_from_loop == 0:
                        img = cv2.resize(frame, None, fx=0.25, fy=0.25)
                        cv2.imwrite(
                            f"./temp/thumbnails/{frame_number}.png", img
                        )
                        cv2.imwrite(
                            f"./temp/first_last_scene_frames/{frame_number}.png",
                            frame,
                        )
                        which_frame_from_loop += 1
                    elif which_frame_from_loop == 1:
                        cv2.imwrite(
                            f"./temp/first_last_scene_frames/{frame_number}.png",
                            frame,
                        )
                        which_frame_from_loop -= 1

    def read_text_from_image(self, image_path):
        found_text = [
            list(
                filter(
                    None,
                    pytesseract.image_to_string(
                        Image.open(image_path),
                        lang="eng",
                    ).splitlines(),
                )
            )
        ]
        return found_text

    def open_image_convert_and_save(self, image_path, frame_number):
        img = Image.open(image_path)
        width, height = img.size
        frame = cv2.imread(image_path)
        grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(
            grayscale, 230, 255, cv2.THRESH_BINARY_INV
        )
        cropped_img_r = threshold[
            0 : int(height * 0.2), int(width * 0.75) : int(width)
        ]
        cv2.imwrite(
            f"./temp/first_last_scene_frames/frame_{frame_number}.png",
            cropped_img_r,
        )

    def generate_vfx_text(
        self,
        potential_frames_ranges_with_vfx_text,
        frames_with_embedded_text_id,
    ):
        found_vfx_text = {}
        frames_not_found = []
        found_vfx_flag = False
        print("\n-Reading VFX text-")
        for frame_range in tqdm(
            potential_frames_ranges_with_vfx_text,
            desc="Frames checked",
            unit="frames",
        ):
            numbers_to_check = self.evenly_spaced_nums_from_range(
                frame_range, q_nums=5, endpoint=False
            )
            for frame_id in numbers_to_check:
                if frame_id in frames_with_embedded_text_id:
                    if found_vfx_flag is True:
                        found_vfx_flag = False
                        break
                    if frame_id < frame_range[0]:
                        continue
                    if frame_id > frame_range[1] - 1:
                        break
                    try:
                        image = f"./temp/text_imgs/frame_{frame_id}.png"
                        text = self.read_text_from_image(image)
                        for line in text:
                            if not line:
                                continue
                            matched_text = self.match_text(
                                line[0], beginning_chars="VFX"
                            )
                            if matched_text:
                                found_vfx_flag = True
                                first_frame_of_scene = frame_range[0]
                                last_frame_of_scene = frame_range[1] - 1

                                right_first_image = f"./temp/first_last_scene_frames/{first_frame_of_scene}.png"
                                right_last_image = f"./temp/first_last_scene_frames/{last_frame_of_scene}.png"
                                try:
                                    # TODO look into it
                                    self.open_image_convert_and_save(
                                        right_first_image, first_frame_of_scene
                                    )
                                    first_frame_tc = self.read_text_from_image(
                                        f"./temp/first_last_scene_frames/frame_{first_frame_of_scene}.png"
                                    )
                                    first_frame_tc = (
                                        self.tc_cleanup_from_potential_errors(
                                            tc_text=first_frame_tc,
                                            frame_number=first_frame_of_scene,
                                        )
                                    )
                                except FileNotFoundError as e:
                                    frames_not_found.append(
                                        first_frame_of_scene
                                    )
                                    logging.exception(
                                        f"Error with frame {first_frame_of_scene}:\n %s",
                                        e,
                                    )
                                try:
                                    self.open_image_convert_and_save(
                                        right_last_image, last_frame_of_scene
                                    )
                                    last_frame_tc = self.read_text_from_image(
                                        f"./temp/first_last_scene_frames/frame_{last_frame_of_scene}.png"
                                    )
                                    last_frame_tc = (
                                        self.tc_cleanup_from_potential_errors(
                                            tc_text=last_frame_tc,
                                            frame_number=last_frame_of_scene,
                                        )
                                    )
                                    tc_out = self.read_tc_add_one_frame(
                                        last_frame_tc
                                    )
                                except FileNotFoundError as e:
                                    frames_not_found.append(
                                        last_frame_of_scene
                                    )
                                    logging.exception(
                                        f"Error with frame {last_frame_of_scene}:\n %s",
                                        e,
                                    )
                                    tc_out = last_frame_tc
                                except ValueError as e:
                                    logging.exception(
                                        f"Error with frame {last_frame_of_scene}:\n %s",
                                        e,
                                    )
                                    tc_out = last_frame_tc
                                if first_frame_of_scene not in found_vfx_text:
                                    found_vfx_text[first_frame_of_scene] = {}
                                    found_vfx_text[first_frame_of_scene][
                                        "TEXT"
                                    ] = matched_text
                                    found_vfx_text[first_frame_of_scene][
                                        "TC IN"
                                    ] = first_frame_tc
                                    found_vfx_text[first_frame_of_scene][
                                        "TC OUT"
                                    ] = tc_out
                                    found_vfx_text[first_frame_of_scene][
                                        "FRAME OUT"
                                    ] = frame_range[1]
                    except FileNotFoundError as e:
                        frames_not_found.append(frame_id)
                        logging.exception(
                            f"Error with frame {frame_id}:\n %s", e
                        )
                        continue
        if frames_not_found:
            print(
                f"Error with frames: {str(frames_not_found)[1:-1]}. Search may be incomplete."
            )
        return found_vfx_text

    def check_previous_frames(
        self, frames_with_embedded_text_id, frame, found_adr_text
    ):
        index = frames_with_embedded_text_id.index(frame)
        for curr_frame in frames_with_embedded_text_id[index - 1 :: -1]:
            image = f"./temp/text_imgs/frame_{curr_frame}.png"
            text = self.read_text_from_image(image)
            for line in text:
                if not line:
                    break
                matched_text = self.match_text(line[0], beginning_chars="ADR")
                if matched_text:
                    right_image = f"./temp/tc_imgs/frame_{curr_frame}.png"
                    frame_tc = self.read_text_from_image(right_image)
                    try:
                        frame_tc = self.tc_cleanup_from_potential_errors(
                            tc_text=frame_tc, frame_number=curr_frame
                        )
                    except ValueError as e:
                        logging.exception(
                            f"Error with frame {curr_frame}:\n %s", e
                        )
                        frame_tc = "WRONG TC"
                    if curr_frame not in found_adr_text:
                        found_adr_text[curr_frame] = {}
                        found_adr_text[curr_frame]["TEXT"] = matched_text
                        found_adr_text[curr_frame]["TC"] = frame_tc
                else:
                    return found_adr_text
        return found_adr_text

    def check_next_frames(
        self, frames_with_embedded_text_id, frame, found_adr_text
    ):
        index = frames_with_embedded_text_id.index(frame)
        for curr_frame in frames_with_embedded_text_id[index + 1 :]:
            image = f"./temp/text_imgs/frame_{curr_frame}.png"
            text = self.read_text_from_image(image)
            for line in text:
                if not line:
                    break
                matched_text = self.match_text(line[0], beginning_chars="ADR")
                if matched_text:
                    right_image = f"./temp/tc_imgs/frame_{curr_frame}.png"
                    frame_tc = self.read_text_from_image(right_image)
                    try:
                        frame_tc = self.tc_cleanup_from_potential_errors(
                            tc_text=frame_tc, frame_number=curr_frame
                        )
                    except ValueError as e:
                        logging.exception(
                            f"Error with frame {curr_frame}:\n %s", e
                        )
                        frame_tc = "WRONG TC"
                    if curr_frame not in found_adr_text:
                        found_adr_text[curr_frame] = {}
                        found_adr_text[curr_frame]["TEXT"] = matched_text
                        found_adr_text[curr_frame]["TC"] = frame_tc
                else:
                    return found_adr_text
        return found_adr_text

    def generate_adr_text(self, frames_with_embedded_text_id):
        found_adr_text = {}
        print("\n-Searching for ADR text-")
        # pbar = tqdm(
        #     total=len(frames_with_embedded_text_id),
        #     desc="Frames checked",
        #     unit="frames",
        # )
        for frame in tqdm(
            frames_with_embedded_text_id[::15],
            desc="Frames checked",
            unit="frames",
        ):
            # print(frame)
            left_image = f"./temp/text_imgs/frame_{frame}.png"
            text = self.read_text_from_image(left_image)
            for line in text:
                if not line:
                    continue
                matched_text = self.match_text(line[0], beginning_chars="ADR")
                if matched_text:
                    right_image = f"./temp/tc_imgs/frame_{frame}.png"
                    frame_tc = self.read_text_from_image(right_image)
                    # pbar.set_postfix_str(
                    #     f"Last text found: {text[0]}", refresh=True
                    # )
                    try:
                        frame_tc = self.tc_cleanup_from_potential_errors(
                            tc_text=frame_tc, frame_number=frame
                        )
                    except ValueError as e:
                        logging.exception(f"Error with frame {frame}:\n %s", e)
                        frame_tc = "WRONG TC"
                    if frame not in found_adr_text:
                        found_adr_text[frame] = {}
                        found_adr_text[frame]["TEXT"] = matched_text
                        found_adr_text[frame]["TC"] = frame_tc
                        previous_frames = self.check_previous_frames(
                            frames_with_embedded_text_id, frame, found_adr_text
                        )
                        next_frames = self.check_next_frames(
                            frames_with_embedded_text_id, frame, found_adr_text
                        )
                        found_adr_text.update(
                            {**previous_frames, **next_frames}
                        )
            # pbar.update(1)
        sorted_dict = {k: found_adr_text[k] for k in sorted(found_adr_text)}
        found_adr_text = self.remove_all_but_border_cases_found(sorted_dict)
        return found_adr_text

    def remove_all_but_border_cases_found(self, text_dict):
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
            try:
                tc_out = self.read_tc_add_one_frame(text_dict[ranges[1]]["TC"])
            except ValueError as e:
                logging.exception(
                    "Error with frame",
                    e,
                )
                tc_out = text_dict[ranges[1]]["TC"]
            new_adr_dict[ranges[0]] = {}
            new_adr_dict[ranges[0]]["TEXT"] = text_dict[ranges[0]]["TEXT"]
            new_adr_dict[ranges[0]]["TC IN"] = text_dict[ranges[0]]["TC"]
            new_adr_dict[ranges[0]]["TC OUT"] = tc_out
            new_adr_dict[ranges[0]]["FRAME OUT"] = ranges[1] + 1
        return new_adr_dict

    def merge_dicts(self, dict_a, dict_b):
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

    def add_real_timestamps(self, frames_dict):
        for frame_number in frames_dict.keys():
            real_tc_in = self.convert_current_frame_to_tc(frame_number)
            real_tc_out = self.convert_current_frame_to_tc(
                frames_dict[frame_number]["FRAME OUT"]
            )
            frames_dict[frame_number]["REAL TC IN"] = real_tc_in
            frames_dict[frame_number]["REAL TC OUT"] = real_tc_out
        self.close_cap()
        return frames_dict

    def close_cap(self):
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    pass
