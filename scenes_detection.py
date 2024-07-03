"""Module for detecting scenes in a video."""

from typing import List, Tuple
from scenedetect import open_video, SceneManager, AdaptiveDetector
from scenedetect.frame_timecode import FrameTimecode
from files_operations import find_video_file


def detect_all_scenes(
    video_name: str = None,
) -> List[Tuple[FrameTimecode, FrameTimecode]]:
    """Detect all scenes in a video.

    Args:
        video_name (str, optional): Video name. Defaults to None.

    Returns:
        List[Tuple[FrameTimecode, FrameTimecode]]: List of scenes.
    """
    if video_name is not None:
        video = open_video(video_name)
        scene_manager = SceneManager()
        scene_manager.add_detector(AdaptiveDetector())
        print("\n-Detecting scenes-")
        scene_manager.detect_scenes(video=video, show_progress=True)
        scene_list = scene_manager.get_scene_list(start_in_scene=True)
        return scene_list


if __name__ == "__main__":
    video_name = find_video_file()
    scene_list = detect_all_scenes(video_name)
    print(scene_list)
