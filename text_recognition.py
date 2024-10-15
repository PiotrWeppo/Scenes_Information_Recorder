"""Module for text recognition in a video.
It generates pictures with text from a video, detects VFX and ADR text,
and generates a dictionary with the results."""

from typing import List, Tuple, Dict
from collections import Counter
import logging
import re
import cv2
from PIL import Image
import pytesseract
import numpy as np
from tqdm import tqdm

from files_operations import delete_temp_folder_on_error_and_exit
from scenedetect.frame_timecode import FrameTimecode


class TextRecognition:
    """Class for text recognition in a video.
    It generates pictures with text from a video,
    detects VFX and ADR text, and generates a dictionary with the results.

    Args:
        cap (cv2.VideoCapture): Video capture object.
        files_path (str): Path to where the files will be saved.
        video (str): Video name.
        start_frame (int): Video start frame point.
        text_area (List[Tuple[int, int]]): Text area.
        tc_area (List[Tuple[int, int]]): Time code area.
    """

    def __init__(
        self,
        cap: cv2.VideoCapture,
        files_path: str,
        video: str,
        start_frame: int,
        text_area: List[Tuple[int, int]],
        tc_area: List[Tuple[int, int]],
    ) -> None:
        self.cap: cv2.VideoCapture = cap
        self.files_path: str = files_path
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.video_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video: str = video
        self.start_frame: int = start_frame
        self.text_area: List[Tuple[int, int]] = text_area
        self.tc_area: List[Tuple[int, int]] = tc_area

    def convert_current_frame_to_tc(self, frame_number: str) -> str:
        """Converts the current frame number to a time code in format HH:MM:SS:FF.

        Args:
            frame_number (str): Frame number.

        Returns:
            str: Time code in format HH:MM:SS:FF (Hours, Minutes, Seconds, Frame).
        """
        frame_number = int(frame_number)
        fps = int(self.video_fps)

        hours = frame_number // (fps * 60 * 60)
        frame_number %= fps * 60 * 60

        minutes = frame_number // (fps * 60)
        frame_number %= fps * 60

        seconds = frame_number // fps
        frames = frame_number % fps

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    def read_tc_add_one_frame(self, time_str: str) -> str:
        """Reads a time code string and adds one frame to it.

        Args:
            time_str (str): Time code string in format HH:MM:SS:FF
                (Hours:Minutes:Seconds:Frames).

        Returns:
            str: Time code string with one frame added.
        """
        if time_str == "WRONG TC" or time_str == "EMPTY TC":
            return time_str

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

    def tc_cleanup_from_potential_errors(
        self, tc_text: List[str], frame_number: int
    ) -> str:
        """Cleans up the time code text from potential errors.

        If the time code is not in the correct format, it returns "WRONG TC".
        If the time code is empty, it returns "EMPTY TC".
        Searches for pattern in a text and returns the formatted text.

        Args:
            tc_text (List[str]): Time code text.
            frame_number (int): Frame number.

        Returns:
            str: Cleaned up time code text.
        """
        if not tc_text or not tc_text[0]:
            return "EMPTY TC"
        pattern = re.compile(r"(\d{2})")
        joined_text = "".join(tc_text[0])
        try:
            x = re.findall(pattern, joined_text)
            formated_text = f"{x[0]}:{x[1]}:{x[2]}:{x[3]}"
        except IndexError as e:
            logging.exception(
                f"Error with frame {frame_number}. Trying to format and clean"
                f" TC: '{joined_text}'.\n%s",
                e,
            )
            return "WRONG TC"
        return formated_text

    def match_text(self, text: str, beginning_chars: str) -> str:
        """Matches text with a pattern and returns the matched text.

        Args:
            text (str): Text to match.
            beginning_chars (str): Characters from which the text starts.

        Returns:
            str: Matched text. If no match, returns an empty string.
        """
        pattern = re.compile(beginning_chars + r"\s*(.+)", re.IGNORECASE)
        match = re.search(pattern, text)
        if match is None:
            return ""
        else:
            matched_text = match.group()
            return matched_text[:3].upper() + matched_text[3:]

    def evenly_spaced_nums_from_range(
        self,
        range_list: List[List[int]],
        q_nums: int = 3,
        endpoint: bool = True,
        nums_with_borders: bool = True,
    ) -> List[int]:
        """Generates evenly spaced list of numbers from a range.

        Args:
            range_list (List[List[int]]): List with the start and end of
                the range.
            q_nums (int, optional): Quantity of numbers to generate.
                Defaults to 3.
            endpoint (bool, optional): If True, the endpoint is
                included in the range.Defaults to True.
            nums_with_borders (bool, optional): If True, the numbers with
                borders are included. Defaults to True.

        Returns:
            List[int]: List of evenly spaced numbers.
        """
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

    def generate_imgs_with_text_from_video(self) -> List[int]:
        """Processes the video and saves frames with potential text.

        Returns:
            List[int]: List of frame numbers with embedded text.
        """
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)
        logging.debug("Video start frame: %s", self.start_frame)
        frames_with_embedded_text_id = []
        if not self.cap.isOpened():
            delete_temp_folder_on_error_and_exit("Error opening video file")
        print("\n-Saving frames containing potential text-")
        pbar = tqdm(
            total=self.video_length - 1 - self.start_frame,
            desc="Scanned frames",
            unit="frames",
            leave=True,
            ascii=" █",
        )
        frames_counter = 0
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret is True:
                current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES) - 1)
                binary_image = self.frame_processing(frame)
                top_left, _, bottom_right, _ = self.text_area
                cropped_img_l = binary_image[
                    top_left[1] : bottom_right[1],
                    top_left[0] : bottom_right[0],
                ]
                n_black_pix = np.sum(cropped_img_l == 0)
                pbar.set_postfix_str(
                    f"Frames saved: {frames_counter}", refresh=True
                )
                if n_black_pix >= 2000:
                    top_left, _, bottom_right, _ = self.tc_area
                    cropped_img_r = binary_image[
                        top_left[1] : bottom_right[1],
                        top_left[0] : bottom_right[0],
                    ]
                    filename = f"frame_{current_frame}.png"
                    cv2.imwrite(
                        f"{self.files_path}/temp/text_imgs/" + filename,
                        cropped_img_l,
                    )
                    cv2.imwrite(
                        f"{self.files_path}/temp/tc_imgs/" + filename,
                        cropped_img_r,
                    )
                    # frames_with_embedded_text_id.append(int(filename.split(".")[0][6:]))
                    frames_with_embedded_text_id.append(int(current_frame))
                    frames_counter += 1
                pbar.update(1)
            else:
                break
        pbar.close()

        return frames_with_embedded_text_id

    def frame_processing(self, frame: np.ndarray) -> np.ndarray:
        """Applies processing to a frame. Returns a binary image.

        Args:
            frame (np.ndarray): Frame to process.

        Returns:
            np.ndarray: Binary image.
        """
        grayscale = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(
            grayscale, 245, 255, cv2.THRESH_BINARY_INV
        )
        return threshold

    def check_if_scenes_can_contain_text(
        self,
        scene_list: List[Tuple[FrameTimecode, FrameTimecode]],
        frames_with_embedded_text_id: List[int],
    ) -> List[List[int]]:
        """Checks if scenes can contain text.

        Compares found scenes with frames that can contain text.
        If the frames are in the scene, it adds the scene to the list.

        Args:
            scene_list (List[Tuple[FrameTimecode, FrameTimecode]]):
                List of scenes.
            frames_with_embedded_text_id (List[int]):
                List of frame numbers with embedded text.

        Returns:
            List[List[int, int]]: List of potential frames ranges
                with VFX text.
        """
        each_scene_first_last_frame = [
            [int(i[0]), int(i[1])] for i in scene_list
        ]
        each_scene_first_last_frame = self.update_start_frame(
            each_scene_first_last_frame
        )
        numbers_to_check = [
            self.evenly_spaced_nums_from_range(range, q_nums=5, endpoint=False)
            for range in each_scene_first_last_frame
        ]
        potential_frames_ranges_with_vfx_text = []
        for sublist in numbers_to_check:
            if any(frame in frames_with_embedded_text_id for frame in sublist):
                potential_frames_ranges_with_vfx_text.append([
                    each_scene_first_last_frame[
                        numbers_to_check.index(sublist)
                    ][0],
                    each_scene_first_last_frame[
                        numbers_to_check.index(sublist)
                    ][1],
                ])
        print(
            "-Found potential text in"
            f" {len(potential_frames_ranges_with_vfx_text)} scenes-"
        )
        return potential_frames_ranges_with_vfx_text

    def update_start_frame(self, ranges: List[List[int]]) -> List[List[int]]:
        """
        Updates the start frame of the program.

        Args:
        ranges (list of [int, int]): List of ranges represented as [start, end].

        Returns:
        list of [int, int]: Updated list of ranges.
        """
        # Filter out ranges where the end number is smaller than the new number
        updated_ranges = [
            range for range in ranges if range[1] >= self.start_frame
        ]

        # Update the start frame of the range that contain the start frame
        # of the program
        for i, (start, end) in enumerate(updated_ranges):
            if start <= self.start_frame <= end:
                updated_ranges[i][0] = self.start_frame
        return updated_ranges

    def generate_pictures_for_each_scene(
        self, potential_frames_ranges_with_vfx_text: List[List[int]]
    ) -> None:
        """Generates pictures for each scene.

        It generates thumbnails and first and last frames of the scene.
        The pictures are saved in the temp folder.
        The thumbnails are saved in the thumbnails folder,
        and the first and last frames are saved in the
        first_last_scene_frames folder.

        Args:
            potential_frames_ranges_with_vfx_text (List[List[int]]):
                List of potential frames ranges with VFX text.
        """

        print("\n-Generating Pictures-")
        for frame_range in tqdm(
            potential_frames_ranges_with_vfx_text,
            desc="Generated ",
            unit="imgs",
            ascii=" █",
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
                            f"{self.files_path}/temp/thumbnails/{frame_number}.png",
                            img,
                        )
                        cv2.imwrite(
                            f"{self.files_path}/temp/first_last_scene_frames/{frame_number}.png",
                            frame,
                        )
                        which_frame_from_loop += 1
                    elif which_frame_from_loop == 1:
                        cv2.imwrite(
                            f"{self.files_path}/temp/first_last_scene_frames/{frame_number}.png",
                            frame,
                        )
                        which_frame_from_loop -= 1

    def read_text_from_image(self, image_path: str, mode: str) -> List[str]:
        """Reads text from an image.

        Args:
            image_path (str): Image path.
            mode (str): Mode to read. Can be "text" or "tc".

        Returns:
            List[str]: List of found text in the image.
        """
        allowlist = (
            " 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz?!:"
        )
        options_for_text = (
            "--psm 6 -c load_system_dawg=false load_freq_dawg=false"
            f" tessedit_char_whitelist={allowlist}"
        )
        options_for_tc = (
            "--psm 7 -c tessedit_char_whitelist=:0123456789"
            " load_system_dawg=false -c load_freq_dawg=false"
        )
        if mode == "text":
            options = options_for_text
        elif mode == "tc":
            options = options_for_tc
        found_text = [
            list(
                filter(
                    None,
                    pytesseract.image_to_string(
                        Image.open(image_path),
                        lang="eng",
                        config=options,
                    ).splitlines(),
                )
            )
        ]
        return found_text

    def generate_processed_pictures(
        self, image_path: str, frame_number: int
    ) -> None:
        """Processes a frame, crops it, and saves it.

        Args:
            image_path (str): Image path.
            frame_number (int): Frame number.
        """
        frame = cv2.imread(image_path)
        binary_image = self.frame_processing(frame)
        top_left, _, bottom_right, _ = self.tc_area
        cropped_img_r = binary_image[
            top_left[1] : bottom_right[1],
            top_left[0] : bottom_right[0],
        ]
        cv2.imwrite(
            f"{self.files_path}/temp/first_last_scene_frames/frame_{frame_number}.png",
            cropped_img_r,
        )

    def generate_vfx_text(
        self,
        potential_frames_ranges_with_vfx_text: List[List[int]],
        frames_with_embedded_text_id: List[int],
    ) -> Dict[int, Dict[str, str]]:
        """Generates VFX text.

        It reads the text from the images and checks
        if it matches the VFX pattern.
        If it does, it generates a dictionary with the results.

        Args:
            potential_frames_ranges_with_vfx_text (List[List[int]]):
                List of potential frames ranges with VFX text.

            frames_with_embedded_text_id (List[int]):
                List of frame numbers with embedded text.

        Returns:
            Dict[int, Dict[str, str]]: Dictionary with the results.
        """
        found_vfx_text: Dict[int, Dict[str, str]] = {}
        frames_not_found: list = []
        found_vfx_flag: bool = False
        print("\n-Reading VFX text-")
        for frame_range in tqdm(
            potential_frames_ranges_with_vfx_text,
            desc="Frames checked",
            unit="frames",
            ascii=" █",
        ):
            # Chooses a couple of frames from the range to check for VFX text
            numbers_to_check = self.evenly_spaced_nums_from_range(
                frame_range, q_nums=8, endpoint=False
            )
            text_found_in_a_range = []
            for frame_id in numbers_to_check:
                # if frame_id in frames_with_embedded_text_id:
                #     if found_vfx_flag is True:
                #         found_vfx_flag = False
                #         break
                if frame_id < frame_range[0]:
                    continue
                if frame_id > frame_range[1] - 1:
                    break
                try:
                    image = f"{self.files_path}/temp/text_imgs/frame_{frame_id}.png"
                    text = self.read_text_from_image(image, mode="text")
                    if not text:
                        continue
                    text_in_current_frame = []
                    for line in text[0]:
                        matched_text = self.match_text(
                            line, beginning_chars="VFX"
                        )
                        if matched_text:
                            text_in_current_frame.append(matched_text)
                        continue
                    if text_in_current_frame:
                        vfx_text = " \n".join(text_in_current_frame)
                        text_found_in_a_range.append(vfx_text)
                except FileNotFoundError as e:
                    frames_not_found.append(frame_id)
                    logging.exception(f"Error with frame {frame_id}:\n %s", e)
                    continue
            if text_found_in_a_range:
                most_probable_text = self.construct_most_common_word(
                    text_found_in_a_range
                )
                # found_vfx_flag = True
                first_frame_of_scene = frame_range[0]
                last_frame_of_scene = frame_range[1] - 1

                # TODO: Program should check if both frames
                # don't exist already.
                right_first_image = f"{self.files_path}/temp/first_last_scene_frames/{first_frame_of_scene}.png"
                right_last_image = f"{self.files_path}/temp/first_last_scene_frames/{last_frame_of_scene}.png"
                try:
                    # Generates processed pictures in case the
                    # person that crated the video by chance
                    # added the text later in the scene or
                    # removed it before the scene ends.
                    # That way, knowing that there is the text
                    # in the scene, we can check and read TC
                    # from the correct images.
                    self.generate_processed_pictures(
                        right_first_image, first_frame_of_scene
                    )
                    first_frame_tc = self.read_text_from_image(
                        f"{self.files_path}/temp/first_last_scene_frames/frame_{first_frame_of_scene}.png",
                        mode="tc",
                    )
                    first_frame_tc = self.tc_cleanup_from_potential_errors(
                        tc_text=first_frame_tc,
                        frame_number=first_frame_of_scene,
                    )
                except FileNotFoundError as e:
                    frames_not_found.append(first_frame_of_scene)
                    logging.exception(
                        f"Error with frame {first_frame_of_scene}:\n %s",
                        e,
                    )
                try:
                    self.generate_processed_pictures(
                        right_last_image, last_frame_of_scene
                    )
                    last_frame_tc = self.read_text_from_image(
                        f"{self.files_path}/temp/first_last_scene_frames/frame_{last_frame_of_scene}.png",
                        mode="tc",
                    )
                    last_frame_tc = self.tc_cleanup_from_potential_errors(
                        tc_text=last_frame_tc,
                        frame_number=last_frame_of_scene,
                    )
                    tc_out = self.read_tc_add_one_frame(last_frame_tc)
                except FileNotFoundError as e:
                    frames_not_found.append(last_frame_of_scene)
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
                    ] = most_probable_text
                    found_vfx_text[first_frame_of_scene][
                        "TC IN"
                    ] = first_frame_tc
                    found_vfx_text[first_frame_of_scene]["TC OUT"] = tc_out
                    found_vfx_text[first_frame_of_scene]["FRAME OUT"] = (
                        frame_range[1]
                    )
        if frames_not_found:
            print(
                f"Couldn't find frames: {str(frames_not_found)[1:-1]}. Search"
                " may be incomplete."
            )
        return found_vfx_text

    def check_previous_or_next_frames(
        self,
        frames_to_check: List[int],
        frame: int,
        found_adr_text: Dict[int, Dict[str, str]],
        mode: str,
    ) -> Dict[int, Dict[str, str]]:
        """Checks the previous or next frames for ADR text.

        If it finds it, it generates a dictionary with the results.

        Args:
            frames_to_check (List[int]):
                List of frame numbers with embedded text.

            frame (int): Frame number.

            found_adr_text (Dict[int, Dict[str, str]]):
                Dictionary with the results.

            mode (str): Mode to check. Can be "previous" or "next".

        Returns:
            Dict[int, Dict[str, str]]: Dictionary with the results.
            int, optional: New index.
        """
        index = frames_to_check.index(frame)
        if mode == "previous":
            sliced_list = frames_to_check[index - 1 :: -1]
        elif mode == "next":
            sliced_list = frames_to_check[index + 1 :]
        boundry = False
        last_frame = None
        # Only check for text in consecutive frames
        for curr_frame in sliced_list:
            if last_frame is not None:
                if abs(curr_frame - last_frame) > 1:
                    break
            image = f"{self.files_path}/temp/text_imgs/frame_{curr_frame}.png"
            text = self.read_text_from_image(image, mode="text")
            # If no text or reached boundry, break the loop
            if not text or boundry:
                break
            found_any_adr = False
            for line in text[0]:
                matched_text = self.match_text(line, beginning_chars="ADR")
                if matched_text:
                    found_any_adr = True
                    right_image = f"{self.files_path}/temp/tc_imgs/frame_{curr_frame}.png"
                    frame_tc = self.read_text_from_image(
                        right_image, mode="tc"
                    )
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
            # Text can hold multiple values
            # If not one of the values is ADR, break the loop
            if not found_any_adr:
                boundry = True
            last_frame = curr_frame
        if mode == "next":
            new_index = frames_to_check.index(curr_frame)
            return found_adr_text, new_index
        else:
            return found_adr_text

    def generate_adr_text(
        self, frames_with_embedded_text_id: List[int]
    ) -> Dict[int, Dict[str, str]]:
        """Reads the text from the images. Generates ADR text.

        Args:
            frames_with_embedded_text_id (List[int]):
                List of frame numbers with embedded text.

        Returns:
            Dict[int, Dict[str, str]]: Dictionary with the results.
        """
        frames_to_check = frames_with_embedded_text_id.copy()
        found_adr_text: Dict[int, Dict[str, str]] = {}
        print("\n-Searching for ADR text-")
        # for frame in tqdm(
        #     frames_to_check[::15],
        #     desc="Frames checked",
        #     unit="frames",
        # ):
        pbar = tqdm(
            total=len(frames_to_check),
            desc="Frames checked",
            unit="frames",
            leave=True,
            ascii=" █",
        )
        i = 0
        while i < len(frames_to_check):
            frame = frames_to_check[i]
            left_image = f"{self.files_path}/temp/text_imgs/frame_{frame}.png"
            text = self.read_text_from_image(left_image, mode="text")
            # If empty text, continue to the next frame
            if not text:
                i += 15
                pbar.update(15)
                continue
            returning_from_next_boundry = False
            for line in text[0]:
                matched_text = self.match_text(line, beginning_chars="ADR")
                if matched_text:
                    right_image = (
                        f"{self.files_path}/temp/tc_imgs/frame_{frame}.png"
                    )
                    frame_tc = self.read_text_from_image(
                        right_image, mode="tc"
                    )
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
                        previous_frames = self.check_previous_or_next_frames(
                            frames_to_check,
                            frame,
                            found_adr_text,
                            mode="previous",
                        )
                        next_frames, new_index = (
                            self.check_previous_or_next_frames(
                                frames_to_check,
                                frame,
                                found_adr_text,
                                mode="next",
                            )
                        )
                        returning_from_next_boundry = True
                        i = new_index + 15
                        diff = abs(new_index - i)
                        pbar.update(diff + 15)
                        found_adr_text.update(
                            {**previous_frames, **next_frames}
                        )
            if not returning_from_next_boundry:
                i += 15
                pbar.update(15)
        # pbar.update(1)
        sorted_dict = {k: found_adr_text[k] for k in sorted(found_adr_text)}
        found_adr_text = self.remove_all_but_border_cases_found(sorted_dict)
        return found_adr_text

    def remove_all_but_border_cases_found(
        self, text_dict: Dict[int, Dict[str, str]]
    ) -> Dict[int, Dict[str, str]]:
        """Removes all but the border cases from the found text.

        It keeps only the first and last frame of the found text.
        It also adds the real time code to the dictionary.

        Args:
            text_dict (Dict[int, Dict[str, str]]): Dictionary with the results.

        Returns:
            Dict[int, Dict[str, str]]: Dictionary with the results.
        """
        keys_series = []
        first_and_last_key = []
        new_adr_dict = {}
        for i in text_dict.keys():
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
            # Temp dictionary with specific ADR text found
            # temp_dict = {
            #     key: value
            #     for key, value in text_dict.items()
            #     if ranges[0] <= key <= ranges[1]
            # }
            # text_values = [details["TEXT"] for details in temp_dict.values()]
            text_values = [
                details["TEXT"]
                for key, details in text_dict.items()
                if ranges[0] <= key <= ranges[1]
            ]
            most_probable_text = self.construct_most_common_word(text_values)
            new_adr_dict[ranges[0]] = {}
            new_adr_dict[ranges[0]]["TEXT"] = most_probable_text
            new_adr_dict[ranges[0]]["TC IN"] = text_dict[ranges[0]]["TC"]
            new_adr_dict[ranges[0]]["TC OUT"] = tc_out
            new_adr_dict[ranges[0]]["FRAME OUT"] = ranges[1] + 1
        return new_adr_dict

    def construct_most_common_word(
        self,
        text_values: List[str],
    ) -> str:
        """Constructs the most common word from the list of words.

        Takes the most common character from each found text,
            and constructs the most likely to occur word.

        Args:
            text_values (List[str]): List of found text.

        Returns:
            str: Most common word constructed from the text dictionary.
        """
        max_length = max(len(s) for s in text_values)
        padded_strings = [s.ljust(max_length) for s in text_values]
        result_string = ""
        transposed_list = zip(*padded_strings)

        for characters in transposed_list:
            most_common_char, _ = Counter(characters).most_common(1)[0]
            result_string += most_common_char

        return result_string.rstrip()

    def merge_dicts(
        self,
        dict_a: Dict[int, Dict[str, str]],
        dict_b: Dict[int, Dict[str, str]],
    ) -> Dict[int, Dict[str, str]]:
        """Merges two dictionaries.
        If the keys are the same, it merges the values.
        If the keys are different, it keeps the values.
        It also sorts the results.

        Args:
            dict_a (Dict[int, Dict[str, str]]): First dictionary.
            dict_b (Dict[int, Dict[str, str]]): Second dictionary.

        Returns:
            Dict[int, Dict[str, str]]: Dictionary with the results.
        """
        merge_result: Dict[int, Dict[str, str]] = {}
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

    def add_real_timestamps(
        self, frames_dict: Dict[int, Dict[str, str]]
    ) -> Dict[int, Dict[str, str]]:
        """Adds the real time code to the dictionary.
        It converts the frame numbers to time codes.

        Args:
            frames_dict (Dict[int, Dict[str, str]]): Dictionary with the
                results.

        Returns:
            Dict[int, Dict[str, str]]: Dictionary with the results.
        """
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
        """Close the video capture object and destroy all windows."""
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    pass
