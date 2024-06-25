import tkinter as tk
import cv2
from PIL import Image, ImageTk


cap = None
text_rect_clicks = []
tc_rect_clicks = []
video_label = None
scale_third_screen = None
current_button = None
text_button = None
tc_button = None


def get_or_init_cap(video_path="TEST_C.mp4"):
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(video_path)
    return cap


def clear_frame():
    for widget in frame.winfo_children():
        widget.destroy()


def show_first_frame():
    """Set the video to the first frame and display it."""
    global cap
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(
                frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST
            )
            cv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.configure(image=imgtk)
        else:
            print("Failed to read the first frame.")


def setup_third_screen():
    global video_label
    global scale_third_screen
    global text_button, tc_button
    clear_frame()

    title_label_third = tk.Label(
        frame, text="Set program detection areas", font=("Arial", 16)
    )
    title_label_third.grid(row=0, column=0)

    message = """
    Select one of the buttons and then press twice on the screen diagonally across the smallest area where all the text can fit.
    Only this area will be analyzed by the program. The slider below the screen can help you see if the largest area has been selected.
    """
    messageVar = tk.Message(frame, text=message, width=1000, justify="left")
    messageVar.grid(row=1, column=0)

    cap = get_or_init_cap()
    max_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    video_label = tk.Label(frame)
    video_label.grid(row=2, column=0)
    show_first_frame()

    third_screen_frame = tk.Frame(frame)
    third_screen_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

    from_label = tk.Label(third_screen_frame, text="0")
    from_label.grid(row=0, column=0, padx=(0, 5), sticky="w")

    scale_third_screen = tk.Scale(
        third_screen_frame, from_=0, to=(max_frames - 1), orient=tk.HORIZONTAL
    )
    scale_third_screen.grid(row=0, column=1, sticky="ew")

    to_label = tk.Label(third_screen_frame, text=str(max_frames))
    to_label.grid(row=0, column=2, padx=(5, 0), sticky="e")

    third_screen_frame.columnconfigure(1, weight=1)

    buttons_frame = tk.Frame(frame)
    buttons_frame.grid(row=4, column=0, sticky="ew", padx=300)

    frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(0, weight=1)
    buttons_frame.grid_columnconfigure(1, weight=1)

    text_button = tk.Button(
        buttons_frame,
        text="VFX/ADR text area",
        bg="green",
        fg="white",
        command=text_button_click,
        width=20,
        font=("Arial", 10, "bold"),
    )
    text_button.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    tc_button = tk.Button(
        buttons_frame,
        text="TC text area",
        bg="blue",
        fg="white",
        command=tc_button_click,
        width=20,
        font=("Arial", 10, "bold"),
    )
    tc_button.grid(row=0, column=1, sticky="ew", padx=(10, 0))

    def show_popup():
        popup = tk.Toplevel()
        popup.title("Warning")
        popup.resizable(0, 0)
        message = tk.Label(
            popup, text="Please make sure to select both areas of detection."
        )
        message.pack(pady=10)
        close_button = tk.Button(popup, text="Close", command=popup.destroy)
        close_button.pack()
        center_window()

    def submit_action():
        if len(text_rect_clicks) != 2 or len(tc_rect_clicks) != 2:
            show_popup()

    submit_btn = tk.Button(
        frame,
        text="Submit",
        command=submit_action,
        font=("Arial", 10, "bold"),
    )
    submit_btn.grid(row=5, column=0, pady=10)

    scale_third_screen.bind(
        "<B1-Motion>", lambda event: update_frame(scale_third_screen.get())
    )
    scale_third_screen.bind(
        "<ButtonRelease-1>",
        lambda event: update_frame(scale_third_screen.get()),
    )

    center_window()


def update_frame(value):
    """Update the displayed frame based on the scale's value."""
    global text_rect_clicks, tc_rect_clicks
    frame_number = int(value)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    ret, frame = cap.read()
    if ret:
        if len(text_rect_clicks) == 2:
            cv2.rectangle(
                frame, text_rect_clicks[0], text_rect_clicks[1], (0, 255, 0), 2
            )  # Green rectangle
        if len(tc_rect_clicks) == 2:
            cv2.rectangle(
                frame, tc_rect_clicks[0], tc_rect_clicks[1], (255, 0, 0), 2
            )  # Blue rectangle
        frame = cv2.resize(
            frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST
        )
        cv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)


def text_button_click():
    global current_button
    current_button = "text_button"
    text_rect_clicks.clear()
    text_button.config(relief="sunken", bg="grey")
    tc_button.config(relief="raised", bg="blue")
    video_label.bind("<Button-1>", on_picture_click)


def tc_button_click():
    global current_button
    current_button = "tc_button"
    tc_rect_clicks.clear()
    tc_button.config(relief="sunken", bg="grey")
    text_button.config(relief="raised", bg="green")
    video_label.bind("<Button-1>", on_picture_click)


def on_picture_click(event):
    """Handle click events on the picture."""
    global text_rect_clicks, tc_rect_clicks, current_button
    global text_button, tc_button
    if current_button == "text_button":
        if len(text_rect_clicks) < 2:
            text_rect_clicks.append((int(event.x * 2), int(event.y * 2)))
    elif current_button == "tc_button":
        if len(tc_rect_clicks) < 2:
            tc_rect_clicks.append((int(event.x * 2), int(event.y * 2)))

    print(text_rect_clicks, tc_rect_clicks)
    print(event.x, event.y)
    if (
        current_button == "text_button"
        and len(text_rect_clicks) == 2
        or current_button == "tc_button"
        and len(tc_rect_clicks) == 2
    ):
        draw_rectangle()
        text_button.config(relief="raised", bg="green")
        tc_button.config(relief="raised", bg="blue")
        video_label.unbind("<Button-1>")


def draw_rectangle():
    """Draw rectangles on the picture using the collected coordinates."""
    global text_rect_clicks, tc_rect_clicks, scale_third_screen
    cap.set(cv2.CAP_PROP_POS_FRAMES, scale_third_screen.get())
    ret, frame = cap.read()
    if ret:
        if len(text_rect_clicks) == 2:
            cv2.rectangle(
                frame, text_rect_clicks[0], text_rect_clicks[1], (0, 255, 0), 2
            )  # Green rectangle for text_button
        if len(tc_rect_clicks) == 2:
            cv2.rectangle(
                frame, tc_rect_clicks[0], tc_rect_clicks[1], (255, 0, 0), 2
            )  # Blue rectangle for tc_button
        frame = cv2.resize(
            frame, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_NEAREST
        )
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = Image.fromarray(frame)
        frame = ImageTk.PhotoImage(image=frame)
        video_label.configure(image=frame)
        video_label.image = frame


def on_submit():
    global video_label
    clear_frame()
    if check_var.get():
        title_label_second = tk.Label(
            frame,
            text="Select the first frame after the title card",
            font=("Arial", 16),
        )
        title_label_second.grid(row=0, column=0)

        message = """
        Some videos include a board at the beginning with a title and other information. We want the program to skip this part in the analysis.
        Position the camera on the first frame after the title card.
        """
        messageVar = tk.Message(
            frame, text=message, width=1000, justify="left"
        )
        messageVar.grid(row=1, column=0)

        cap = get_or_init_cap()
        max_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        video_label = tk.Label(frame)
        video_label.grid(row=2, column=0)
        show_first_frame()

        # Shared IntVar for Scale and Entry
        scale_value = tk.IntVar(value=0)

        second_screen_frame = tk.Frame(frame)
        second_screen_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")

        from_label = tk.Label(second_screen_frame, text="0")
        from_label.grid(row=0, column=0, padx=(0, 5))

        scale_second_screen = tk.Scale(
            second_screen_frame,
            from_=0,
            to=(max_frames - 1),
            orient=tk.HORIZONTAL,
        )
        scale_second_screen.grid(row=0, column=1, sticky="ew")

        to_label = tk.Label(second_screen_frame, text=str(max_frames - 1))
        to_label.grid(row=0, column=2, padx=(5, 0))

        second_screen_frame.columnconfigure(1, weight=1)

        def update_frame_2(value):
            frame_number = int(value)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
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
                video_label.imgtk = imgtk
                video_label.configure(image=imgtk)
            else:
                print("Failed to retrieve the frame.")

        scale_second_screen.bind(
            "<Motion>", lambda event: update_frame_2(scale_second_screen.get())
        )
        scale_second_screen.bind(
            "<ButtonRelease-1>",
            lambda event: update_frame_2(scale_second_screen.get()),
        )

        def increase_value():
            current_value = scale_second_screen.get()
            if current_value < max_frames:
                new_value = current_value + 1
                scale_second_screen.set(new_value)
                update_frame_2(new_value)

        def decrease_value():
            current_value = scale_second_screen.get()
            if current_value > 0:
                new_value = current_value - 1
                scale_second_screen.set(new_value)
                update_frame_2(new_value)

        buttons_frame2 = tk.Frame(frame)
        buttons_frame2.grid(row=4, column=0, sticky="ew", pady=(0, 5))

        down_button = tk.Button(
            buttons_frame2,
            text="\U0001F808",
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
            text="\U0001F80A",
            command=increase_value,
            width=5,
        )
        up_button.grid(row=0, column=1, sticky="ew", padx=(5, 400))

        buttons_frame2.grid_columnconfigure(0, weight=1)
        buttons_frame2.grid_columnconfigure(1, weight=1)

        entry_box = tk.Entry(frame, textvariable=scale_value)
        entry_box.grid(row=5, column=0, sticky="ew", padx=400)

        def validate_entry(*args):
            try:
                new_value = int(entry_box.get())
                if 0 <= new_value <= max_frames:
                    scale_second_screen.set(
                        new_value
                    )
                    update_frame_2(new_value)
                else:
                    raise ValueError
            except ValueError:
                entry_box.delete(
                    0, tk.END
                )
            finally:
                entry_box.delete(0, tk.END)

        entry_box.bind("<Return>", lambda event: validate_entry())

        submit_btn_new = tk.Button(
            frame,
            text="Submit",
            command=setup_third_screen,
            font=("Arial", 10, "bold"),
        )
        submit_btn_new.grid(row=6, column=0, pady=10)
        center_window()
    else:
        setup_third_screen()


def center_window():
    """Center the window on the screen."""
    root.update_idletasks()
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width / 2) - (window_width / 2))
    y = int((screen_height / 2) - (window_height / 2))
    root.geometry(f"+{x}+{y}")


root = tk.Tk()
root.title("Scenes Information Recorder")
root.resizable(0, 0)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

frame = tk.Frame(root)
frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
frame.columnconfigure(0, weight=1)
frame.rowconfigure(0, weight=1)

message = tk.Label(frame, text="Choose video file:")
message.grid(row=1, column=0)

radio_value = tk.StringVar(value="Option 1")
radio1 = tk.Radiobutton(
    frame, text="Option 1", variable=radio_value, value="Option 1"
)
radio1.grid(row=2, column=0)
radio2 = tk.Radiobutton(
    frame, text="Option 2", variable=radio_value, value="Option 2"
)
radio2.grid(row=3, column=0)

check_var = tk.IntVar()
check_btn = tk.Checkbutton(
    frame, text="Does the film start with a title card?", variable=check_var
)
check_btn.grid(row=4, column=0)

submit_btn = tk.Button(
    frame,
    text="Submit",
    command=on_submit,
    font=("Arial", 10, "bold"),
)
submit_btn.grid(row=5, column=0, pady=10)
center_window()

root.mainloop()
