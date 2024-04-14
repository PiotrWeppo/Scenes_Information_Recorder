from scenedetect import open_video, SceneManager, AdaptiveDetector
from scenedetect.scene_manager import save_images
from files_operations import find_video_file


def detect_all_scenes(video_name=None):
    if video_name is not None:
        video = open_video(video_name)
        scene_manager = SceneManager()
        scene_manager.add_detector(AdaptiveDetector())
        print("\n-Detecting scenes-")
        scene_manager.detect_scenes(video=video, show_progress=True)
        scene_list = scene_manager.get_scene_list(start_in_scene=True)
        # print(scene_list)
        # for i, scene in enumerate(scene_list):
        #     print(
        #         "Scene %2d: Start %s / Frame %d, End %s / Frame %d"
        #         % (
        #             i + 1,
        #             scene[0].get_timecode(),
        #             scene[0].get_frames(),
        #             scene[1].get_timecode(),
        #             scene[1].get_frames(),
        #         )
        #     )
        return scene_list


def create_scenes_pictures(scene_list, video_name=None):
    if video_name is not None:
        video = open_video(video_name)
        print("\n-Saving pictures from scenes-")
        # img_paths = save_images(
        #     scene_list=scene_list,
        #     video=video,
        #     num_images=2,
        #     show_progress=True,
        #     # encoder_param=50,
        #     output_dir="./Scene_pictures",
        #     image_extension="png",
        # )
        print("\n-Saving thumbnails from scenes-")
        save_images(
            scene_list=scene_list,
            video=video,
            num_images=3,
            show_progress=True,
            encoder_param=3,
            output_dir="./Scene_thumbnails",
            image_extension="png",
            width=500,
            height=281,
        )


if __name__ == "__main__":
    video_name = find_video_file()
    scene_list = detect_all_scenes(video_name)
    print(scene_list)
