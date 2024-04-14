from text_recognition import (
    generate_imgs_with_text_from_video,
    check_if_vfx_in_found_scenes,
    generate_thumbnails_for_each_scene,
    generate_vfx_text,
    generate_adr_text,
    merge_dicts,
    add_real_timestamps,
)
from files_operations import (
    find_video_file,
    create_folder,
)
from scenes_detection import detect_all_scenes


video = find_video_file()
create_folder("./temp/text_imgs", "./temp/tc_imgs", "./temp/thumbnails")
frames_with_embedded_text_id = generate_imgs_with_text_from_video(video)
scene_list = detect_all_scenes(video)
# print(scene_list)
frames_ranges_with_vfx_text = check_if_vfx_in_found_scenes(
    scene_list, frames_with_embedded_text_id
)
# print(frames_with_embedded_text_id)
generate_thumbnails_for_each_scene(video, frames_ranges_with_vfx_text)
found_vfx_text = generate_vfx_text(frames_ranges_with_vfx_text, video)
# print(found_vfx_text)
found_adr_text = generate_adr_text(frames_with_embedded_text_id, video)
# print(found_adr_text)
merged_text_dict = merge_dicts(found_vfx_text, found_adr_text)
# print(merged_text_dict)
final_text_dict = add_real_timestamps(merged_text_dict, video)
print(final_text_dict)