import pytest
import cv2
from text_recognition import TextRecognition


class TestTextRecognition:

    text_rec = TextRecognition(
        video="TEST_C.mp4",
        cap=cv2.VideoCapture("TEST_C.mp4"),
        files_path="./save_folder/",
        start_frame=0,
        text_area=None,
        tc_area=None,
    )

    @property
    def fps(self):
        return self.text_rec.video_fps

    ##########################################################################
    # text_convert_current_frame_to_tc()

    @pytest.fixture
    def fixture_convert_current_frame_based_on_fps(self):
        if self.fps == 24:
            return [
                ("0", "00:00:00:00"),
                ("24", "00:00:01:00"),
                ("240", "00:00:10:00"),
                ("1440", "00:01:00:00"),
                ("14400", "00:10:00:00"),
                ("86400", "01:00:00:00"),
            ]
        elif self.fps == 25:
            return [
                ("0", "00:00:00:00"),
                ("250", "00:00:10:00"),
                ("1500", "00:01:00:00"),
                ("15000", "00:10:00:00"),
                ("90000", "01:00:00:00"),
            ]

    def test_convert_current_frame_to_tc(
        self, fixture_convert_current_frame_based_on_fps
    ):
        for element, expected in fixture_convert_current_frame_based_on_fps:
            assert (
                self.text_rec.convert_current_frame_to_tc(element) == expected
            )

    ##########################################################################
    # read_tc_add_one_frame()

    @pytest.fixture
    def fixture_read_tc_add_one_frame(self):
        if self.fps == 24:
            return [
                ("00:00:00:00", "00:00:00:01"),
                ("00:00:00:23", "00:00:01:00"),
                ("00:00:15:15", "00:00:15:16"),
                ("00:00:59:23", "00:01:00:00"),
                ("00:59:59:23", "01:00:00:00"),
            ]
        elif self.fps == 25:
            return [
                ("00:00:00:00", "00:00:00:01"),
                ("00:00:00:24", "00:00:01:00"),
                ("00:00:15:15", "00:00:15:16"),
                ("00:00:59:24", "00:01:00:00"),
                ("00:59:59:24", "01:00:00:00"),
            ]

    def test_read_tc_add_one_frame(self, fixture_read_tc_add_one_frame):
        for element, expected in fixture_read_tc_add_one_frame:
            assert self.text_rec.read_tc_add_one_frame(element) == expected

    ##########################################################################
    # tc_cleanup_from_potential_errors

    @pytest.mark.parametrize(
        "element,expected",
        [
            ([[]], "EMPTY TC"),
            ([["01:02:03:20"]], "01:02:03:20"),
            ([["10 04 05:12"]], "10:04:05:12"),
            ([["0020 03:12"]], "00:20:03:12"),
            ([["12345678"]], "12:34:56:78"),
            ([["12:02:8:10"]], "WRONG TC"),
            ([["12:02 10"]], "WRONG TC"),
            ([["1"]], "WRONG TC"),
        ],
    )
    def test_tc_cleanup_from_potential_errors(self, element, expected):
        assert (
            self.text_rec.tc_cleanup_from_potential_errors(
                element, frame_number=0
            )
            == expected
        )

    ##########################################################################
    # match_text()

    @pytest.mark.parametrize(
        "element,expected",
        [
            ("VFX: 123fsdfr", "VFX: 123fsdfr"),
            ("vfX: abcDE", "VFX: abcDE"),
            ("", ""),
            ("vfX: first VFX: second", "VFX: first VFX: second"),
            ("ADR: 123", ""),
            ("VF X: 123", ""),
            ("fa3542d vFx f432", "VFX f432"),
        ],
    )
    def test_match_text(self, element, expected):
        assert (
            self.text_rec.match_text(element, beginning_chars="VFX")
            == expected
        )

    ##########################################################################
    # remove_all_but_border_cases_found()

    test_dict = {
        1500: {"TEXT": "ADR: Example", "TC": "00:20:00:00"},
        1501: {"TEXT": "ADR: Example", "TC": "00:20:00:01"},
        1502: {"TEXT": "ADR: Example", "TC": "00:20:00:02"},
        1503: {"TEXT": "ADR: Example", "TC": "00:20:00:03"},
        1504: {"TEXT": "ADR: Example", "TC": "00:20:00:04"},
        1505: {"TEXT": "ADR: Example", "TC": "00:20:00:05"},
        1506: {"TEXT": "ADR: Example", "TC": "00:20:00:06"},
        1507: {"TEXT": "ADR: Example", "TC": "00:20:00:07"},
        1508: {"TEXT": "ADR: Example", "TC": "00:20:00:08"},
        1509: {"TEXT": "ADR: Example", "TC": "00:20:00:09"},
        1510: {"TEXT": "ADR: Example", "TC": "00:20:00:10"},
    }

    def test_remove_all_but_border_cases_found(self):
        assert self.text_rec.remove_all_but_border_cases_found(
            self.test_dict
        ) == {
            1500: {
                "TEXT": "ADR: Example",
                "TC IN": "00:20:00:00",
                "TC OUT": "00:20:00:11",
                "FRAME OUT": 1511,
            }
        }

    ##########################################################################
    # construct_most_common_word()

    test_list = [
        "ADR  Exemple",
        "ADR: Example",
        "ADR: Example",
        "ADR: h5234r1s34",
        "ADR: Example",
        "ADR: Examp!?",
        "ADR: Examole",
        "ADR: Examplehdfghd",
        "ADR: Example",
        "ADR: EXample",
        "ADR: Example634573",
    ]

    def test_construct_most_common_word(self):
        assert (
            self.text_rec.construct_most_common_word(self.test_list)
            == "ADR: Example"
        )

    ##########################################################################
    # merge_dicts()

    dict_a = {
        993: {
            "TEXT": "VFX: PHONE INSERT\nVFX: SPLIT SCREEN",
            "TC IN": "00:07:45:08",
            "TC OUT": "00:07:54:01",
            "FRAME OUT": 1202,
        },
        2735: {
            "TEXT": "VFX: CLEANUP",
            "TC IN": "00:08:27:04",
            "TC OUT": "00:08:32:00",
            "FRAME OUT": 2851,
        },
    }

    dict_b = {
        418: {
            "TEXT": "ADR: Aha ok",
            "TC IN": "00:00:12:10",
            "TC OUT": "00:00:13:11",
            "FRAME OUT": 443,
        },
        2833: {
            "TEXT": "ADR: Hmm",
            "TC IN": "00:08:31:06",
            "TC OUT": "00:08:31:23",
            "FRAME OUT": 2850,
        },
    }

    merged_dict = {
        418: {
            "TEXT": "ADR: Aha ok",
            "TC IN": "00:00:12:10",
            "TC OUT": "00:00:13:11",
            "FRAME OUT": 443,
        },
        993: {
            "TEXT": "VFX: PHONE INSERT\nVFX: SPLIT SCREEN",
            "TC IN": "00:07:45:08",
            "TC OUT": "00:07:54:01",
            "FRAME OUT": 1202,
        },
        2735: {
            "TEXT": "VFX: CLEANUP",
            "TC IN": "00:08:27:04",
            "TC OUT": "00:08:32:00",
            "FRAME OUT": 2851,
        },
        2833: {
            "TEXT": "ADR: Hmm",
            "TC IN": "00:08:31:06",
            "TC OUT": "00:08:31:23",
            "FRAME OUT": 2850,
        },
    }

    def test_merge_dicts(self):
        assert (
            self.text_rec.merge_dicts(self.dict_a, self.dict_b)
            == self.merged_dict
        )

    ##########################################################################
    # add_real_timestamps()

    merged_dict = {
        418: {
            "TEXT": "ADR: Aha ok",
            "TC IN": "00:00:12:10",
            "TC OUT": "00:00:13:11",
            "FRAME OUT": 443,
        },
        993: {
            "TEXT": "VFX: PHONE INSERT\nVFX: SPLIT SCREEN",
            "TC IN": "00:07:45:08",
            "TC OUT": "00:07:54:01",
            "FRAME OUT": 1202,
        },
        2735: {
            "TEXT": "VFX: CLEANUP",
            "TC IN": "00:08:27:04",
            "TC OUT": "00:08:32:00",
            "FRAME OUT": 2851,
        },
        2833: {
            "TEXT": "ADR: Hmm",
            "TC IN": "00:08:31:06",
            "TC OUT": "00:08:31:23",
            "FRAME OUT": 2850,
        },
    }

    @pytest.fixture
    def fixture_test_add_real_timestamps(self):
        if self.fps == 24:
            final_dict = {
                418: {
                    "TEXT": "ADR: Aha ok",
                    "TC IN": "00:00:12:10",
                    "TC OUT": "00:00:13:11",
                    "FRAME OUT": 443,
                    "REAL TC IN": "00:00:17:10",
                    "REAL TC OUT": "00:00:18:11",
                },
                993: {
                    "TEXT": "VFX: PHONE INSERT\nVFX: SPLIT SCREEN",
                    "TC IN": "00:07:45:08",
                    "TC OUT": "00:07:54:01",
                    "FRAME OUT": 1202,
                    "REAL TC IN": "00:00:41:09",
                    "REAL TC OUT": "00:00:50:02",
                },
                2735: {
                    "TEXT": "VFX: CLEANUP",
                    "TC IN": "00:08:27:04",
                    "TC OUT": "00:08:32:00",
                    "FRAME OUT": 2851,
                    "REAL TC IN": "00:01:53:23",
                    "REAL TC OUT": "00:01:58:19",
                },
                2833: {
                    "TEXT": "ADR: Hmm",
                    "TC IN": "00:08:31:06",
                    "TC OUT": "00:08:31:23",
                    "FRAME OUT": 2850,
                    "REAL TC IN": "00:01:58:01",
                    "REAL TC OUT": "00:01:58:18",
                },
            }
        elif self.fps == 25:
            final_dict = {
                418: {
                    "TEXT": "ADR: Aha ok",
                    "TC IN": "00:00:12:10",
                    "TC OUT": "00:00:13:11",
                    "FRAME OUT": 443,
                    "REAL TC IN": "00:00:16:18",
                    "REAL TC OUT": "00:00:17:18",
                },
                993: {
                    "TEXT": "VFX: PHONE INSERT\nVFX: SPLIT SCREEN",
                    "TC IN": "00:07:45:08",
                    "TC OUT": "00:07:54:01",
                    "FRAME OUT": 1202,
                    "REAL TC IN": "00:00:39:18",
                    "REAL TC OUT": "00:00:48:02",
                },
                2735: {
                    "TEXT": "VFX: CLEANUP",
                    "TC IN": "00:08:27:04",
                    "TC OUT": "00:08:32:00",
                    "FRAME OUT": 2851,
                    "REAL TC IN": "00:01:49:10",
                    "REAL TC OUT": "00:01:54:01",
                },
                2833: {
                    "TEXT": "ADR: Hmm",
                    "TC IN": "00:08:31:06",
                    "TC OUT": "00:08:31:23",
                    "FRAME OUT": 2850,
                    "REAL TC IN": "00:01:53:08",
                    "REAL TC OUT": "00:01:54:00",
                },
            }
        return final_dict

    def test_add_real_timestamps(self, fixture_test_add_real_timestamps):
        actual_results = self.text_rec.add_real_timestamps(self.merged_dict)
        for frame_number, expected in fixture_test_add_real_timestamps.items():
            assert (
                actual_results[frame_number] == expected
            ), f"Mismatch for frame {frame_number}"

    ##########################################################################
    # update_start_frame()

    text_rec.start_frame = 150

    @pytest.mark.parametrize(
        "test_input,expected",
        [(
            [[0, 100], [100, 200], [200, 300], [300, 400], [400, 500]],
            [[150, 200], [200, 300], [300, 400], [400, 500]]
        )]
    )
    def test_update_start_frame(self, test_input, expected):
        assert self.text_rec.update_start_frame(test_input) == expected

    ##########################################################################
    # generate_imgs_with_text_from_video()

    ##########################################################################
    # frame_processing()

    ##########################################################################
    # check_if_scenes_can_contian_text()

    ##########################################################################
    # generate_pictures_for_each_scene()

    ##########################################################################
    # read_text_from_image()

    ##########################################################################
    # generate_processed_pictures()

    ##########################################################################
    # generate_vfx_text()

    ##########################################################################
    # check_previous_or_next_frames()

    ##########################################################################
    # generate_adr_text()
