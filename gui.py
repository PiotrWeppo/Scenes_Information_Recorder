"""This module contains the GUI class for the program. The GUI is used to select the video file and set the detection areas for the text."""

from typing import Optional, List, Tuple
import tkinter as tk
import cv2
from PIL import Image, ImageTk


class AppGui:
    """
    Class for creating the GUI for the program. The GUI is used to select the video file and set the detection areas for the text.
        Args:
            main_window (tk.Tk): The main window of the program.
            main_frame (tk.Frame): The main frame of the program.
            cap (cv2.VideoCapture): The video capture object.
            video_fps (float): The frames per second of the video.
            text_picture_clicks (List[Tuple[int, int]]): List of coordinates for the text detection area.
            tc_picture_clicks (List[Tuple[int, int]]): List of coordinates for the timecode detection area.
            text_area (List[Tuple[int, int]]): List of coordinates for the text detection area.
            tc_area (List[Tuple[int, int]]): List of coordinates for the timecode detection area.
            video_label (tk.Label): Label for displaying the video frames.
            scale_third_screen (tk.Scale): Scale for selecting the frame to display.
            current_button (str): The current button that is selected.
            text_button (tk.Button): Button for selecting the text detection area.
            tc_button (tk.Button): Button for selecting the timecode detection area.
            submit_btn3 (tk.Button): Button for submitting the detection areas.
            check_var (tk.IntVar): Variable for the check button.
            main_frame (tk.Frame): The main frame of the program.
            video_sources (List[str]): List of video file names.
            radio_value (tk.StringVar): Variable for the radio buttons.
            scale_value (tk.IntVar): Variable for the scale.

    """

    def __init__(self) -> None:
        self.main_window: Optional[tk.Tk] = None
        self.main_frame: Optional[tk.Frame] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self.video_fps: Optional[float] = None
        self.text_picture_clicks: List[Tuple[int, int]] = []
        self.tc_picture_clicks: List[Tuple[int, int]] = []
        self.text_area: Optional[List[Tuple[int, int]]] = None
        self.tc_area: Optional[List[Tuple[int, int]]] = None
        self.video_label: Optional[tk.Label] = None
        self.scale_third_screen: Optional[tk.Scale] = None
        self.current_button: Optional[str] = None
        self.text_button: Optional[tk.Button] = None
        self.tc_button: Optional[tk.Button] = None
        self.submit_btn3: Optional[tk.Button] = None
        self.check_var: Optional[tk.IntVar] = None
        self.main_frame: Optional[tk.Frame] = None
        self.video_sources: Optional[List[str]] = None
        self.radio_value: Optional[tk.StringVar] = None
        self.scale_value: Optional[tk.IntVar] = None

    def create_list_of_video_sources(self) -> int:
        """Create a list of radio buttons for selecting the video source.

        Returns:
            int: The next empty row in the grid.
        """
        self.radio_value = tk.StringVar(value=self.video_sources[0])
        for i, file in enumerate(self.video_sources):
            radio_btn = tk.Radiobutton(
                self.main_frame,
                text=file,
                variable=self.radio_value,
                value=file,
            )
            radio_btn.grid(row=i + 2, column=0)
        next_empty_row = len(self.video_sources) + 3
        return next_empty_row

    def get_or_init_cap(self, video_path: str) -> cv2.VideoCapture:
        """Get the video capture object or initialize it if it does not exist.

        Args:
            video_path (str): The path to the video file.

        Returns:
            cv2.VideoCapture: The video capture object.
        """
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(video_path)
            self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        return self.cap

    def create_main_screen(self, video_names: List[str]) -> None:
        """Create the main screen of the program.

        Args:
            video_names (List[str]): List of video file names.
        """
        self.video_sources = video_names
        self.main_window = tk.Tk()
        self.main_window.title("Scenes Information Recorder")
        self.main_window.resizable(0, 0)
        self.main_window.columnconfigure(0, weight=1)
        self.main_window.rowconfigure(0, weight=1)

        self.main_frame = tk.Frame(self.main_window)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

        message = tk.Label(self.main_frame, text="Choose video file:")
        message.grid(row=1, column=0)

        next_empty_row = self.create_list_of_video_sources()
        # radio1 = tk.Radiobutton(
        #     self.main_frame,
        #     text="Option 1",
        #     variable=self.radio_value,
        #     value="Option 1",
        # )
        # radio1.grid(row=2, column=0)
        # radio2 = tk.Radiobutton(
        #     self.main_frame,
        #     text="Option 2",
        #     variable=self.radio_value,
        #     value="Option 2",
        # )
        # radio2.grid(row=3, column=0)

        self.check_var = tk.IntVar()
        check_btn = tk.Checkbutton(
            self.main_frame,
            text="Does the film start with a title card?",
            variable=self.check_var,
        )
        check_btn.grid(row=next_empty_row, column=0)
        next_empty_row += 1

        submit_btn = tk.Button(
            self.main_frame,
            text="Submit",
            command=self.create_second_screen,
            font=("Arial", 10, "bold"),
        )
        submit_btn.grid(row=next_empty_row, column=0, pady=10)
        self.center_window()
        self.main_window.mainloop()

    def clear_frame(self) -> None:
        """Clear the main frame of the program."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_first_frame(self) -> None:
        """Show the first frame of the video in the GUI."""
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.resize(
                    frame,
                    None,
                    fx=0.5,
                    fy=0.5,
                    interpolation=cv2.INTER_NEAREST,
                )
                cv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv_frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            else:
                print("Failed to read the first frame.")

    def create_second_screen(self) -> None:
        """Create the second screen of the program."""
        self.cap = self.get_or_init_cap(self.radio_value.get())
        self.video_name = self.radio_value.get()
        self.clear_frame()
        if self.check_var.get():
            title_label_second = tk.Label(
                self.main_frame,
                text="Select the first frame after the title card",
                font=("Arial", 16),
            )
            title_label_second.grid(row=0, column=0)

            message = """
            Some videos include a board at the beginning with a title and other information. We want the program to skip this part in the analysis.
            Position the camera on the first frame after the title card.
            """
            message_sec_screen = tk.Message(
                self.main_frame, text=message, width=1000, justify="left"
            )
            message_sec_screen.grid(row=1, column=0)

            max_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

            self.video_label = tk.Label(self.main_frame)
            self.video_label.grid(row=2, column=0)
            self.show_first_frame()

            # Shared IntVar for Scale and Entry
            self.scale_value = tk.IntVar(value=0)

            second_screen_frame = tk.Frame(self.main_frame)
            second_screen_frame.grid(
                row=3, column=0, padx=10, pady=5, sticky="ew"
            )

            from_label = tk.Label(second_screen_frame, text="0")
            from_label.grid(row=0, column=0, padx=(0, 5))

            scale_second_screen = tk.Scale(
                second_screen_frame,
                from_=0,
                to=(max_frames - 1),
                orient=tk.HORIZONTAL,
                variable=self.scale_value,
            )
            scale_second_screen.grid(row=0, column=1, sticky="ew")

            to_label = tk.Label(second_screen_frame, text=str(max_frames - 1))
            to_label.grid(row=0, column=2, padx=(5, 0))

            second_screen_frame.columnconfigure(1, weight=1)

            def update_frame_2(value: int) -> None:
                """Update the displayed frame based on the scale's value.

                Args:
                    value (int): The value of the scale.
                """
                frame_number = int(value)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = self.cap.read()
                if ret:
                    frame = cv2.resize(
                        frame,
                        None,
                        fx=0.5,
                        fy=0.5,
                        interpolation=cv2.INTER_NEAREST,
                    )
                    cv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv_frame)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.video_label.imgtk = imgtk
                    self.video_label.configure(image=imgtk)
                else:
                    print("Failed to retrieve the frame.")

            scale_second_screen.bind(
                "<Motion>",
                lambda event: update_frame_2(scale_second_screen.get()),
            )
            scale_second_screen.bind(
                "<ButtonRelease-1>",
                lambda event: update_frame_2(scale_second_screen.get()),
            )

            def increase_value() -> None:
                """Increase the value of the scale by 1."""
                current_value = scale_second_screen.get()
                if current_value < max_frames:
                    new_value = current_value + 1
                    scale_second_screen.set(new_value)
                    update_frame_2(new_value)

            def decrease_value() -> None:
                """Decrease the value of the scale by 1."""
                current_value = scale_second_screen.get()
                if current_value > 0:
                    new_value = current_value - 1
                    scale_second_screen.set(new_value)
                    update_frame_2(new_value)

            buttons_frame2 = tk.Frame(self.main_frame)
            buttons_frame2.grid(row=4, column=0, sticky="ew", pady=(0, 5))

            down_button = tk.Button(
                buttons_frame2,
                text="\U0001f808",
                command=decrease_value,
                width=5,
            )
            down_button.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=(400, 5),
            )

            up_button = tk.Button(
                buttons_frame2,
                text="\U0001f80a",
                command=increase_value,
                width=5,
            )
            up_button.grid(row=0, column=1, sticky="ew", padx=(5, 400))

            buttons_frame2.grid_columnconfigure(0, weight=1)
            buttons_frame2.grid_columnconfigure(1, weight=1)

            entry_box = tk.Entry(
                self.main_frame,
                # textvariable=self.scale_value
            )
            entry_box.grid(row=5, column=0, sticky="ew", padx=400)

            # def validate_entry(*args) -> None:
            #     try:
            #         new_value = int(entry_box.get())
            #         if 0 <= new_value <= max_frames:
            #             scale_second_screen.set(new_value)
            #             update_frame_2(new_value)
            #         else:
            #             raise ValueError
            #     except ValueError:
            #         entry_box.delete(0, tk.END)
            #     finally:
            #         entry_box.delete(0, tk.END)

            # entry_box.bind("<Return>", lambda event: validate_entry())

            def validate_entry(*args: str) -> None:
                """Validate the entry box input and update the scale."""
                start_frame = 0
                try:
                    new_value = entry_box.get()
                    if new_value == "":
                        start_frame = 0
                    if new_value.isdigit():
                        start_frame = int(new_value)
                    elif ":" in new_value:
                        try:
                            seconds, frames = map(int, new_value.split(":"))
                            start_frame = int(
                                seconds * self.video_fps + frames
                            )
                        except ValueError:
                            pass
                    if 0 <= start_frame <= max_frames:
                        scale_second_screen.set(start_frame)
                        update_frame_2(start_frame)
                    else:
                        raise ValueError
                except ValueError:
                    pass
                finally:
                    entry_box.delete(0, tk.END)

            entry_box.bind("<Return>", lambda event: validate_entry())

            submit_btn_new = tk.Button(
                self.main_frame,
                text="Submit",
                command=self.create_third_screen,
                font=("Arial", 10, "bold"),
            )
            submit_btn_new.grid(row=6, column=0, pady=10)
            self.center_window()
        else:
            self.create_third_screen()

    def create_third_screen(self) -> None:
        """Create the third screen of the program."""
        self.clear_frame()

        title_label_third = tk.Label(
            self.main_frame,
            text="Set program detection areas",
            font=("Arial", 16),
        )
        title_label_third.grid(row=0, column=0)

        message = """
        Select one of the buttons and then press twice on the screen diagonally across the smallest area where all the text can fit.
        Only this area will be analyzed by the program. The slider below the screen can help you see if the largest area has been selected.
        """
        message_third_screen = tk.Message(
            self.main_frame, text=message, width=1000, justify="left"
        )
        message_third_screen.grid(row=1, column=0)

        max_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.video_label = tk.Label(self.main_frame)
        self.video_label.grid(row=2, column=0)
        self.show_first_frame()

        third_screen_frame = tk.Frame(self.main_frame)
        third_screen_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        from_label = tk.Label(third_screen_frame, text="0")
        from_label.grid(row=0, column=0, padx=(0, 5), sticky="w")

        self.scale_third_screen = tk.Scale(
            third_screen_frame,
            from_=0,
            to=(max_frames - 1),
            orient=tk.HORIZONTAL,
        )
        self.scale_third_screen.grid(row=0, column=1, sticky="ew")

        to_label = tk.Label(third_screen_frame, text=str(max_frames))
        to_label.grid(row=0, column=2, padx=(5, 0), sticky="e")

        third_screen_frame.columnconfigure(1, weight=1)

        buttons_frame = tk.Frame(self.main_frame)
        buttons_frame.grid(row=4, column=0, sticky="ew", padx=300)

        self.main_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

        self.text_button = tk.Button(
            buttons_frame,
            text="VFX/ADR text area",
            bg="green",
            fg="white",
            command=self.text_button_click,
            width=20,
            font=("Arial", 10, "bold"),
        )
        self.text_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.tc_button = tk.Button(
            buttons_frame,
            text="TC text area",
            bg="blue",
            fg="white",
            command=self.tc_button_click,
            width=20,
            font=("Arial", 10, "bold"),
        )
        self.tc_button.grid(row=0, column=1, sticky="ew", padx=(10, 0))

        self.submit_btn3 = tk.Button(
            self.main_frame,
            text="Submit",
            command=self.submit_action,
            font=("Arial", 10, "bold"),
        )
        self.submit_btn3.grid(row=5, column=0, pady=10)

        self.scale_third_screen.bind(
            "<B1-Motion>",
            lambda event: self.update_frame(self.scale_third_screen.get()),
        )
        self.scale_third_screen.bind(
            "<ButtonRelease-1>",
            lambda event: self.update_frame(self.scale_third_screen.get()),
        )

        self.center_window()

    def submit_action(self) -> None:
        """Submit the detection areas and close the program."""
        if (
            len(self.text_picture_clicks) != 2
            or len(self.tc_picture_clicks) != 2
        ):
            self.show_popup()
        else:
            self.text_area = self.calculate_rectangle_corners(
                self.text_picture_clicks
            )
            self.tc_area = self.calculate_rectangle_corners(
                self.tc_picture_clicks
            )
            self.main_window.destroy()

    def show_popup(self) -> None:
        """Show a warning popup if the detection areas are not selected."""
        popup = tk.Toplevel()
        popup.title("Warning")
        popup.resizable(0, 0)
        message = tk.Label(
            popup,
            text="Please make sure to select both areas of detection.",
        )
        message.pack(pady=10)
        close_button = tk.Button(popup, text="Close", command=popup.destroy)
        close_button.pack()
        self.center_window()

    def update_frame(self, value: int) -> None:
        """Update the displayed frame based on the scale's value.

        Args:
            value (int): The value of the scale.
        """
        frame_number = int(value)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        if ret:
            if len(self.text_picture_clicks) == 2:
                cv2.rectangle(
                    frame,
                    self.text_picture_clicks[0],
                    self.text_picture_clicks[1],
                    (0, 255, 0),
                    2,
                )  # Green rectangle
            if len(self.tc_picture_clicks) == 2:
                cv2.rectangle(
                    frame,
                    self.tc_picture_clicks[0],
                    self.tc_picture_clicks[1],
                    (255, 0, 0),
                    2,
                )  # Blue rectangle
            frame = cv2.resize(
                frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST
            )
            cv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

    def text_button_click(self) -> None:
        """Handle click events on the text button."""
        self.current_button = "text_button"
        self.text_picture_clicks.clear()
        self.text_button.config(relief="sunken", bg="grey")
        self.tc_button.config(relief="raised", bg="blue")
        self.video_label.bind("<Button-1>", self.on_picture_click)

    def tc_button_click(self) -> None:
        """Handle click events on the timecode button."""
        self.current_button = "tc_button"
        self.tc_picture_clicks.clear()
        self.tc_button.config(relief="sunken", bg="grey")
        self.text_button.config(relief="raised", bg="green")
        self.video_label.bind("<Button-1>", self.on_picture_click)

    def on_picture_click(self, event: tk.Event) -> None:
        """Handle click events on the picture.

        Args:
            event (tk.Event): The event object.
        """
        if self.current_button == "text_button":
            if len(self.text_picture_clicks) < 2:
                self.text_picture_clicks.append(
                    (int(event.x * 2), int(event.y * 2))
                )
        elif self.current_button == "tc_button":
            if len(self.tc_picture_clicks) < 2:
                self.tc_picture_clicks.append(
                    (int(event.x * 2), int(event.y * 2))
                )

        if (
            self.current_button == "text_button"
            and len(self.text_picture_clicks) == 2
            or self.current_button == "tc_button"
            and len(self.tc_picture_clicks) == 2
        ):
            self.draw_rectangle()
            self.text_button.config(relief="raised", bg="green")
            self.tc_button.config(relief="raised", bg="blue")
            self.video_label.unbind("<Button-1>")

    def draw_rectangle(self) -> None:
        """Draw rectangles on the picture using the collected coordinates."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.scale_third_screen.get())
        ret, frame = self.cap.read()
        if ret:
            if len(self.text_picture_clicks) == 2:
                cv2.rectangle(
                    frame,
                    self.text_picture_clicks[0],
                    self.text_picture_clicks[1],
                    (0, 255, 0),
                    2,
                )  # Green rectangle for text_button
            if len(self.tc_picture_clicks) == 2:
                cv2.rectangle(
                    frame,
                    self.tc_picture_clicks[0],
                    self.tc_picture_clicks[1],
                    (255, 0, 0),
                    2,
                )  # Blue rectangle for tc_button
            frame = cv2.resize(
                frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST
            )
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            frame = ImageTk.PhotoImage(image=frame)
            self.video_label.configure(image=frame)
            self.video_label.image = frame

    def calculate_rectangle_corners(
        self, clicks: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Calculate all four corners of the rectangle based on the two clicked points.

        Args:
            clicks (List[Tuple[int, int]]): List of clicked points.

        Returns:
            List[Tuple[int, int]]: List of all four corners of the rectangle.
        """
        x1, y1 = clicks[0]
        x2, y2 = clicks[1]

        min_x = min(x1, x2)
        max_x = max(x1, x2)
        min_y = min(y1, y2)
        max_y = max(y1, y2)

        top_left = (min_x, min_y)
        top_right = (max_x, min_y)
        bottom_left = (min_x, max_y)
        bottom_right = (max_x, max_y)

        rectangle_corners = [top_left, top_right, bottom_right, bottom_left]
        return rectangle_corners

    def center_window(self) -> None:
        """Center the window on the screen."""
        self.main_window.update_idletasks()
        window_width = self.main_window.winfo_width()
        window_height = self.main_window.winfo_height()
        screen_width = self.main_window.winfo_screenwidth()
        screen_height = self.main_window.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.main_window.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    pass
    # gui = AppGui()
    # gui.create_main_screen()
