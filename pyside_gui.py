from collections import deque
import signal
import cv2
import sys
import os

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QLineEdit,
    QGroupBox,
    QCheckBox,
    QFileDialog,
    QSpacerItem,
    QSizePolicy,
    QMessageBox,
)
from PySide6.QtCore import (
    QThread,
    Qt,
    Signal,
    Slot,
    QSize,
    QRect,
    QPoint,
)
from PySide6.QtGui import (
    QImage,
    QPixmap,
    QFont,
    QPalette,
    QColor,
    QIcon,
    QPainter,
    QPen,
    QGuiApplication,
    QScreen,
)

pyqt_signal = Signal
pyqt_slot = Slot


class Thread(QThread):
    change_pixmap = pyqt_signal(QImage)

    def __init__(self, cap, parent=None):
        super(Thread, self).__init__(parent)
        self.frame_queue = deque(maxlen=1)  # Queue to hold frame numbers
        self.cap = cap
        self.first_frame = True
        self.h, self.w, self.ch, self.bytes_per_line = 0, 0, 0, 0

    def run(self):
        while self.frame_queue:
            frame_number = (
                self.frame_queue.popleft()
            )  # Get the oldest frame number
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.cap.read()
            if ret:
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if self.first_frame:
                    self.h, self.w, self.ch = rgb_image.shape
                    self.bytes_per_line = self.ch * self.w
                    self.first_frame = False
                convert_to_qt_format = QImage(
                    rgb_image.data,
                    self.w,
                    self.h,
                    self.bytes_per_line,
                    QImage.Format_RGB888,
                )
                # p = convert_to_qt_format.scaled(1280, 720, Qt.KeepAspectRatio)
                self.change_pixmap.emit(convert_to_qt_format)

    def setFrameNumber(self, frame_number):
        self.frame_queue.append(
            frame_number
        )  # Add new frame number to the queue

    def stop(self):
        print("Thread is stopping")
        self.isRunning = False
        # self.cap.release()
        self.quit()
        self.terminate()


class VideoContainer(QWidget):
    def __init__(self, video_path, start_frame=0, parent_window=None):
        super().__init__()
        self.video_path = video_path
        self.start_frame = start_frame
        self.parent_window = parent_window
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # self.cap.release()
        self.image_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.image_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # self.resize(1200, 800)
        # screen = QGuiApplication.primaryScreen().availableGeometry()
        # print(f"Screen width: {screen.width()}, height: {screen.height()}")
        # max_width = screen.width() * 0.5
        # max_height = screen.height() * 0.5
        # self.resize(min(self.image_width, max_width), min(self.image_height, max_height))
        self.setMinimumSize(1280, 720)
        self.resize(1280, 720)
        self.start_point = None
        self.end_point = None
        self.rectangles = {}
        self.text_areas = {}
        self.first_time = True
        self.init_ui()
        self.is_drawing = False
        self.button_1_clicked = False
        self.button_2_clicked = False

    @pyqt_slot(QImage)
    def setImage(self, image):
        if image:
            # print(f"Window width: {self.width()}, height: {self.height()}")
            # print(f"Image width: {image.width()}, height: {image.height()}")
            label_size = self.label.size()
            # print(f"{label_size}=")
            # Fresh image from slider
            scaled_image = image.scaled(
                label_size.width(),
                label_size.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.image = QPixmap.fromImage(scaled_image)
            self.clean_image = self.image.copy()
            self.try_draw_rectangles(self.image)
            # update image
            self.label.setPixmap(self.image)

    def changeFrame(self, value):
        self.thread.setFrameNumber(
            value
        )  # Pass the slider value to the thread
        if self.first_time:
            self.thread.start()
            self.first_time = False

    def init_ui(self):
        # self.resize(1200, 800)
        # screen = QGuiApplication.primaryScreen().availableGeometry()
        # print(f"Screen width: {screen.width()}, height: {screen.height()}")
        # max_width = screen.width() * 0.2
        # max_height = screen.height() * 0.2

        self.label = QLabel(self)
        # self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setMinimumSize(1280, 720)
        self.label.resize(1280, 720)
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        # self.label.resize(min(self.image_width, max_width), min(self.image_height, max_height))
        self.thread = Thread(self.cap, self)
        self.thread.change_pixmap.connect(self.setImage)
        self.changeFrame(self.start_frame)  # Start with frame 0
        self.setLayout(layout)
        self.show()

    def resizeEvent(self, event):
        # Update UI elements based on the new size
        if self.label.pixmap() is not None:
            self.setImage(self.label.pixmap().toImage())

    def mousePressEvent(self, event):
        if (
            self.button_1_clicked or self.button_2_clicked
        ) and event.button() == Qt.LeftButton:
            if self.label.geometry().contains(event.position().toPoint()):
                adjusted_point = event.position() - self.label.pos()
                constrained_point = self.constrainPointToImageBounds(
                    adjusted_point.toPoint()
                )
                self.start_point = self.adjustPointForScaling(
                    constrained_point
                )
                self.end_point = self.start_point
                self.is_drawing = True
                self.update()

    def mouseMoveEvent(self, event):
        if (
            self.button_1_clicked or self.button_2_clicked
        ) and self.is_drawing:
            adjusted_point = event.position() - self.label.pos()
            constrained_point = self.constrainPointToImageBounds(
                adjusted_point.toPoint()
            )
            self.end_point = self.adjustPointForScaling(constrained_point)
            self.update()

    def mouseReleaseEvent(self, event):
        if (
            self.button_1_clicked or self.button_2_clicked
        ) and event.button() == Qt.LeftButton:
            adjusted_point = event.position() - self.label.pos()
            constrained_point = self.constrainPointToImageBounds(
                adjusted_point.toPoint()
            )
            self.end_point = self.adjustPointForScaling(constrained_point)
            self.is_drawing = False
            self.update()
            rect = QRect(self.start_point, self.end_point)
            if self.button_1_clicked:
                self.rectangles["VFX/ADR"] = rect
                self.text_areas["VFX/ADR"] = self.calculate_rectangle_corners()
            elif self.button_2_clicked:
                self.rectangles["TC"] = rect
                self.text_areas["TC"] = self.calculate_rectangle_corners()
            # print(self.calculate_rectangle_corners())
            self.button_1_clicked = False
            self.button_2_clicked = False
            self.parent_window.button1.setEnabled(True)
            self.parent_window.button2.setEnabled(True)

    def adjustPointForScaling(self, point):
        label_size = self.label.size()
        image_size = self.image.size()
        scale_x = image_size.width() / label_size.width()
        scale_y = image_size.height() / label_size.height()
        return QPoint(int(point.x() * scale_x), int(point.y() * scale_y))

    def paintEvent(self, event):
        if self.is_drawing:
            temp_image = self.clean_image.copy()
            self.try_draw_rectangles(temp_image)
            temp_painter = QPainter(temp_image)
            if self.button_1_clicked:
                temp_painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
            elif self.button_2_clicked:
                temp_painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
            rect = QRect(self.start_point, self.end_point)
            temp_painter.drawRect(rect)
            temp_painter.end()
            self.label.setPixmap(temp_image)

    def try_draw_rectangles(self, image):
        if self.rectangles:
            temp_painter = QPainter(image)
            for key, value in self.rectangles.items():
                if value is not None:
                    if key == "VFX/ADR":
                        temp_painter.setPen(QPen(Qt.green, 2, Qt.SolidLine))
                    elif key == "TC":
                        temp_painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                    temp_painter.drawRect(value)
            temp_painter.end()

    def calculate_rectangle_corners(self):
        label_size = self.label.size()
        image_size_width, image_size_height = (
            self.image_width,
            self.image_height,
        )

        # Calculate the scaling factor
        scale_factor = min(
            label_size.width() / image_size_width,
            label_size.height() / image_size_height,
        )

        # Calculate the offset to center the image within the QLabel
        offset_x = (label_size.width() - image_size_width * scale_factor) / 2
        offset_y = (label_size.height() - image_size_height * scale_factor) / 2

        # Adjust start and end points for scaling and offset
        x1 = (self.start_point.x() - offset_x) / scale_factor
        y1 = (self.start_point.y() - offset_y) / scale_factor
        x2 = (self.end_point.x() - offset_x) / scale_factor
        y2 = (self.end_point.y() - offset_y) / scale_factor

        # Ensure coordinates are within the bounds of the original image
        x1 = max(0, min(x1, image_size_width))
        y1 = max(0, min(y1, image_size_height))
        x2 = max(0, min(x2, image_size_width))
        y2 = max(0, min(y2, image_size_height))

        # Calculate the true corners of the rectangle
        min_x = int(min(x1, x2))
        max_x = int(max(x1, x2))
        min_y = int(min(y1, y2))
        max_y = int(max(y1, y2))

        top_left = (min_x, min_y)
        top_right = (max_x, min_y)
        bottom_left = (min_x, max_y)
        bottom_right = (max_x, max_y)

        rectangle_corners = [top_left, top_right, bottom_right, bottom_left]
        return rectangle_corners

    def toggleButtonClicked(self, button_number):
        if button_number == 1:
            self.button_1_clicked = not self.button_1_clicked
            clicked = self.button_1_clicked
        elif button_number == 2:
            self.button_2_clicked = not self.button_2_clicked
            clicked = self.button_2_clicked
        else:
            return

        if clicked:
            self.clearRectangle()
            self.parent_window.button1.setEnabled(False)
            self.parent_window.button2.setEnabled(False)

    def clearRectangle(self):
        self.is_drawing = False
        self.start_point = None
        self.end_point = None
        if self.button_1_clicked:
            self.rectangles["VFX/ADR"] = None
        elif self.button_2_clicked:
            self.rectangles["TC"] = None
        # Optionally, if you're displaying the image on a QLabel
        temp_image = self.clean_image.copy()
        self.try_draw_rectangles(temp_image)
        self.label.setPixmap(temp_image)

    def constrainPointToImageBounds(self, point):
        label_size = self.label.size()
        x = max(0, min(point.x(), label_size.width() - 1))
        y = max(0, min(point.y(), label_size.height() - 1))
        return QPoint(x, y)


class MainWindow(QWidget):
    data_signal = Signal(dict)  # Add this line

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.file_name = None
        self.init_ui()
        self.toggleTheme()
        self.resize(800, 600)  # Set the initial size of the window to 800x600

    def showEvent(self, event):
        self.centerWindow()
        super().showEvent(event)

    def centerWindow(self):
        center = QScreen.availableGeometry(
            QApplication.primaryScreen()
        ).center()
        geo = self.frameGeometry()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def init_ui(self):
        # Main layout
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.toggle_theme_button = QPushButton(self)
        self.toggle_theme_button.setIcon(
            QIcon("./resources/images/dark_mode.png")
        )  # Set the icon
        self.toggle_theme_button.setIconSize(
            QSize(30, 30)
        )  # Adjust icon size as needed
        self.toggle_theme_button.clicked.connect(self.toggleTheme)
        self.dark_mode = True  # Track the theme state

        # Add spacer and button to the top layout
        top_layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        top_layout.addWidget(self.toggle_theme_button)

        # Add the top layout to the main layout
        layout.addLayout(top_layout)

        # Welcome text
        welcome_label = QLabel(
            "-Welcome to Scenes Information Recorder for Video Editors-", self
        )
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)

        # Load the image
        title_logo_pixmap = QPixmap("./resources/images/title_logo.jpeg")
        # Scale the image to fit within 200x200 pixels, maintaining aspect ratio
        scaled_pixmap = title_logo_pixmap.scaled(
            500, 500, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # Create a QLabel for the image
        title_logo_label = QLabel(self)
        title_logo_label.setPixmap(scaled_pixmap)
        title_logo_label.setAlignment(Qt.AlignCenter)  # Center the image

        # Add the QLabel to the layout, below the welcome_label
        layout.addWidget(title_logo_label)

        file_group_box = QGroupBox(self)
        file_group_box_layout = QVBoxLayout()

        choose_file_label = QLabel("Choose video file.", self)
        file_group_box_layout.addWidget(choose_file_label)

        choose_file_layout = QHBoxLayout()
        self.file_button = QPushButton("Browse", self)
        self.file_button.clicked.connect(self.browseFile)
        self.file_line_edit = QLineEdit(self)
        choose_file_layout.addWidget(self.file_button)
        choose_file_layout.addWidget(self.file_line_edit)

        # Add the choose_file_layout to the group box layout
        file_group_box_layout.addLayout(choose_file_layout)

        # Set the layout for the group box
        file_group_box.setLayout(file_group_box_layout)

        # Add the group box to the main layout instead of adding choose_file_label and choose_file_layout directly
        layout.addWidget(file_group_box)

        dest_group_box = QGroupBox()
        dest_group_box_layout = QVBoxLayout()

        # Choose destination for saving additional files section
        choose_dest_label = QLabel(
            "Choose destination for saving files (default: video source path)",
            self,
        )
        dest_group_box_layout.addWidget(choose_dest_label)
        choose_dest_layout = QHBoxLayout()
        self.dest_button = QPushButton("Browse", self)
        self.dest_button.clicked.connect(self.browseFolder)
        self.dest_line_edit = QLineEdit(self)
        choose_dest_layout.addWidget(self.dest_button)
        choose_dest_layout.addWidget(self.dest_line_edit)
        dest_group_box_layout.addLayout(choose_dest_layout)

        dest_group_box.setLayout(dest_group_box_layout)
        layout.addWidget(dest_group_box)
        # Add a checkbox for title card query below the second Browse button
        self.title_card_checkbox = QCheckBox(
            "Film starts with the title card", self
        )
        self.title_card_checkbox.setFont(QFont("Arial", 10, QFont.Bold))
        self.title_card_checkbox.setStyleSheet(
            "QCheckBox { padding-top: 20px; }"
        )
        layout.addWidget(self.title_card_checkbox)

        self.save_pictures_checkbox = QCheckBox(
            "Save High-Res pictures from scenes that have VFX text", self
        )
        self.save_pictures_checkbox.setFont(QFont("Arial", 10, QFont.Bold))
        self.save_pictures_checkbox.setStyleSheet(
            "QCheckBox { padding-bottom: 20px; }"
        )
        layout.addWidget(self.save_pictures_checkbox)

        # Submit button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.on_submit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)
        self.setWindowTitle("Scenes Information Recorder")

        self.third_window = None

    def browseFile(self):
        file_filter = (
            "Video Files (*.avi *.mp4 *.mov *.mkv *.flv *.wmv *.mpeg)"
        )
        self.file_name, _ = QFileDialog.getOpenFileName(
            self, "Choose a video file", filter=file_filter
        )
        if self.file_name:
            self.file_line_edit.setText(self.file_name)
            # If dest_line_edit is empty, set its value to the directory of the chosen file
            if not self.dest_line_edit.text():
                file_dir = os.path.dirname(self.file_name)
                self.dest_line_edit.setText(file_dir)

    def browseFolder(self):
        folder_name = QFileDialog.getExistingDirectory(
            self, "Choose a saving destination folder"
        )
        if folder_name:
            self.dest_line_edit.setText(folder_name)

    def on_submit(self):
        # Check if both file_line_edit and dest_line_edit are filled
        if not self.file_line_edit.text() or not self.dest_line_edit.text():
            # Display popup prompting to fill both entry boxes
            QMessageBox.warning(
                self,
                "Incomplete Information",
                "Please fill both fields.",
            )
        elif self.title_card_checkbox.isChecked():
            self.go_to_second_screen()
        else:
            self.go_to_third_screen()

    def go_to_second_screen(self):
        self.second_window = SecondWindow(
            video_path=self.file_line_edit.text(),
            save_hq_pics=self.save_pictures_checkbox.isChecked(),
        )
        self.second_window.data_signal.connect(
            self.handle_data_from_third_window,
        )
        self.second_window.show_main_window.connect(
            self.show
        )  # Connect the signal
        self.second_window.show()
        self.close()  # Close the MainWindow

    def go_to_third_screen(self):
        self.third_window = ThirdWindow(
            video_path=self.file_line_edit.text(),
            save_hq_pics=self.save_pictures_checkbox.isChecked(),
        )
        self.third_window.data_signal.connect(
            self.handle_data_from_third_window
        )
        self.third_window.show_second_window.connect(
            self.show
        )  # Connect the signal
        self.third_window.show()
        self.close()

    def handle_data_from_third_window(self, data):
        data["files_save_dir"] = self.dest_line_edit.text()
        self.data_signal.emit(data)  # Propagate the signal

    def toggleTheme(self):
        if self.dark_mode:
            apply_dark_theme(self.app)
            self.toggle_theme_button.setIcon(
                QIcon("./resources/images/light_mode.png")
            )
        else:
            apply_light_theme(self.app)
            self.toggle_theme_button.setIcon(
                QIcon("./resources/images/dark_mode.png")
            )
        self.dark_mode = not self.dark_mode
    
    def closeEvent(self, event):
        if event.spontaneous():  # If triggered by the user
            reply = QMessageBox.question(
                self,
                "Quit Application",
                "Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


class SecondWindow(QWidget):
    data_signal = Signal(dict)

    show_main_window = Signal()

    def __init__(self, video_path, save_hq_pics=False, parent=None):
        super().__init__(parent)
        self.third_window = None
        self.video_path = video_path
        self.save_hq_pics = save_hq_pics
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Get total frame count
        # self.cap.release()
        self.init_ui()

    def showEvent(self, event):
        self.centerWindow()
        super().showEvent(event)

    def centerWindow(self):
        center = QScreen.availableGeometry(
            QApplication.primaryScreen()
        ).center()
        geo = self.frameGeometry()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def init_ui(self):
        layout = QVBoxLayout()
        self.setWindowTitle("Choose Video Start Point")

        # Button to go back to the main screen
        back_layout = QHBoxLayout()
        back_button = QPushButton("Back", self)
        back_button.clicked.connect(self.onBackClicked)
        back_layout.addWidget(back_button)
        back_layout.addStretch()
        layout.addLayout(back_layout)

        # Centered text
        message = """
        Some videos include a board at the beginning with a title and other information. We want the program to skip this part in the analysis.
        Position the camera on the first frame after the title card.
        If the film does not start with a title card, click Submit to proceed.
        """
        text_label = QLabel(text=message)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        self.video_screen = VideoContainer(self.video_path, parent_window=self)
        layout.addWidget(self.video_screen)

        # screen = VideoContainer()
        # layout.addWidget(screen)
        vertical_padding = QSpacerItem(20, 20, QSizePolicy.Minimum)
        layout.addItem(vertical_padding)

        # Slider with labels
        slider_layout = QHBoxLayout()
        left_label = QLabel("0")
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(0)
        self.slider.setMaximum(
            self.total_frames - 1
        )  # Set slider maximum to total frame count
        self.slider.valueChanged[int].connect(self.changeFrame)
        right_label = QLabel(str(self.total_frames - 1))
        slider_layout.addWidget(left_label)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(right_label)
        layout.addLayout(slider_layout)

        # Label displayed above the slider
        self.slider_label = QLabel(self)
        self.slider_label.setAlignment(Qt.AlignCenter)

        line_edit_HBoxLayout = QHBoxLayout()
        # Create QLineEdit for input
        self.line_edit = QLineEdit()
        self.line_edit.setMaxLength(6)
        self.line_edit.setFixedWidth(100)  # Adjust width as needed

        # Connect QLineEdit signal to slot
        self.line_edit.editingFinished.connect(self.update_slider_position)

        # Step 2: Add a stretch to center the line_edit horizontally
        line_edit_HBoxLayout.addStretch(
            1
        )  # Add stretch before to push the widget to the center
        line_edit_HBoxLayout.addWidget(self.line_edit)  # Add the line_edit
        line_edit_HBoxLayout.addStretch(
            1
        )  # Add stretch after to ensure it stays centered

        # Step 4: Add the QHBoxLayout to the QVBoxLayout
        layout.addLayout(line_edit_HBoxLayout)

        arrows_box_layout = QHBoxLayout()
        arrows_box_layout.addStretch()

        # Create QPushButton for decrementing
        decrement_button = QPushButton("▼")
        decrement_button.setFixedWidth(30)  # Adjust width as needed
        decrement_button.clicked.connect(self.decrementValue)

        # Create QPushButton for incrementing
        increment_button = QPushButton("▲")
        increment_button.setFixedWidth(30)  # Adjust width as needed
        increment_button.clicked.connect(self.incrementValue)

        # Add QLineEdit and QPushButtons to the layout
        arrows_box_layout.addWidget(decrement_button)
        arrows_box_layout.addWidget(increment_button)

        # Add stretch below to ensure the doubleSpinBox stays centered
        arrows_box_layout.addStretch()

        # Add the arrows_box_layout to the main layout
        layout.addLayout(arrows_box_layout)

        # Submit button
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.go_to_third_screen)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def update_slider_position(self):
        try:
            value = self.line_edit.text()
            if value and value.isdigit():
                frame = int(value)
            elif ":" in value:
                try:
                    seconds, frames = map(int, value.split(":"))
                    frame = int(seconds * self.video_fps + frames)
                except ValueError:
                    pass
            self.slider.setValue(frame)
            self.line_edit.clear()
        except UnboundLocalError:
            pass  # Handle the case where the input is not a valid integer

    def incrementValue(self):
        current_value = self.slider.value()
        new_value = current_value + 1
        self.slider.setValue(new_value)

    def decrementValue(self):
        current_value = self.slider.value()
        new_value = current_value - 1
        self.slider.setValue(new_value)

    def onBackClicked(self):
        self.show_main_window.emit()
        self.close()

    def go_to_third_screen(self):
        self.third_window = ThirdWindow(
            video_path=self.video_path,
            save_hq_pics=self.save_hq_pics,
            start_frame=self.slider.value(),
        )
        self.third_window.data_signal.connect(
            self.handle_data_from_third_window
        )
        self.third_window.show_second_window.connect(self.show)
        self.third_window.show()
        self.close()

    def handle_data_from_third_window(self, data):
        self.data_signal.emit(data)  # Propagate the signal to MainWindow

    def update_slider_label_postion(self):
        value = self.slider.value()
        value_str = str(value)
        label_width = max(
            30, 10 * len(value_str)
        )  # Example: base width of 30, plus 10 pixels per character

        self.slider_label.setFixedWidth(label_width)
        slider_width = self.slider.width()
        min_value = self.slider.minimum()
        max_value = self.slider.maximum()
        handle_x = (
            (value - min_value) / (max_value - min_value)
        ) * slider_width
        handle_width_estimate = 15
        label_x = (
            self.slider.x()
            + handle_x
            - (label_width // 2)
            + (handle_width_estimate // 2)
        )
        label_y = self.slider.y() - 25

        self.slider_label.move(label_x, label_y)
        self.slider_label.setText(value_str)

    def resizeEvent(self, event):
        self.update_slider_label_postion()
        event.accept()  # Call the base class method to ensure the event is properly handled

    def changeFrame(self, value):
        self.update_slider_label_postion()
        self.video_screen.thread.setFrameNumber(value)
        self.video_screen.thread.start()

    def closeEvent(self, event):
        if event.spontaneous():  # If triggered by the user
            reply = QMessageBox.question(
                self,
                "Quit Application",
                "Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()


class ThirdWindow(QWidget):

    show_second_window = Signal()
    data_signal = Signal(dict)

    def __init__(
        self, video_path, start_frame=0, save_hq_pics=False, parent=None
    ):
        super().__init__(parent)
        self.video_path = video_path
        self.start_frame = start_frame
        self.save_hq_pics = save_hq_pics
        self.cap = cv2.VideoCapture(self.video_path)
        self.total_frames = int(
            self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        )  # Get total frame count
        self.init_ui()
        self.centerWindow()
        self.data = {}

    def showEvent(self, event):
        self.centerWindow()
        super().showEvent(event)

    def centerWindow(self):
        center = QScreen.availableGeometry(
            QApplication.primaryScreen()
        ).center()
        geo = self.frameGeometry()
        geo.moveCenter(center)
        self.move(geo.topLeft())

    def init_ui(self):
        layout = QVBoxLayout()
        self.setWindowTitle("Set Video VFX/ADR and TC Regions")

        # Button to go back to the main screen
        back_layout = QHBoxLayout()
        back_button = QPushButton("Back", self)
        back_button.clicked.connect(self.onBackClicked)
        back_layout.addWidget(back_button)
        back_layout.addStretch()
        layout.addLayout(back_layout)

        # Centered text
        message = """
        Select one of the buttons and then drag the mouse on the screen diagonally across the smallest area where all the text can fit.
        Then do the same with the other button.
        Only this area will be analyzed by the program. You can use the slider below the screen to see if the border overlaps the text somewhere in the footage.
        """
        text_label = QLabel(text=message)
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        self.video_screen = VideoContainer(
            self.video_path, start_frame=self.start_frame, parent_window=self
        )
        layout.addWidget(self.video_screen, alignment=Qt.AlignCenter)
        vertical_padding = QSpacerItem(20, 20, QSizePolicy.Minimum)
        layout.addItem(vertical_padding)

        slider_layout = QHBoxLayout()
        left_label = QLabel(f"{self.start_frame}")
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setMinimum(self.start_frame)
        self.slider.setMaximum(
            self.total_frames - 1
        )  # Set slider maximum to total frame count
        self.slider.valueChanged[int].connect(self.changeFrame)
        right_label = QLabel(str(self.total_frames - 1))
        slider_layout.addWidget(left_label)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(right_label)
        layout.addLayout(slider_layout)

        # Label displayed above the slider
        self.slider_label = QLabel(self)
        self.slider_label.setAlignment(Qt.AlignCenter)

        # Two centered buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self.button1 = QPushButton("VFX/ADR Text")
        self.button2 = QPushButton("TC Text")
        # Set button1 to be green
        self.button1.setStyleSheet("""
            QPushButton {background-color: green;}
            QPushButton:disabled {background-color: gray;}
        """)
        self.button2.setStyleSheet("""
            QPushButton {background-color: blue;}
            QPushButton:disabled {background-color: gray;}
        """)
        # Ensure both buttons have the same width
        fixedWidth = 150
        self.button1.setFixedWidth(fixedWidth)
        self.button2.setFixedWidth(fixedWidth)
        self.button1.clicked.connect(lambda: self.onButtonClicked(1))
        self.button2.clicked.connect(lambda: self.onButtonClicked(2))
        buttons_layout.addWidget(self.button1)
        buttons_layout.addWidget(self.button2)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Submit button
        submit_button = QPushButton("Submit", self)
        submit_button.clicked.connect(self.closeThirdWindow)
        layout.addWidget(submit_button)

        self.setLayout(layout)

    def onButtonClicked(self, button_number):
        self.button1.setEnabled(False)
        self.button2.setEnabled(False)
        self.video_screen.toggleButtonClicked(button_number)

    def onBackClicked(self):
        self.show_second_window.emit()  # Emit the signal when back_button is clicked
        self.close()

    def closeThirdWindow(self):
        rectangles = self.video_screen.rectangles
        if len(rectangles) == 2 and all(
            rect is not None for rect in rectangles.values()
        ):
            self.data["video_path"] = self.video_screen.video_path
            self.data["start_frame"] = self.video_screen.start_frame
            self.data["text_areas"] = self.video_screen.text_areas
            self.data["cv2_cap_obj"] = self.cap
            self.data["save_hq_pics"] = self.save_hq_pics
            self.data_signal.emit(self.data)
            self.close()
        else:
            QMessageBox.warning(
                self, "Warning", "Choose both VFX/ADR and TC regions."
            )

    def closeEvent(self, event):
        if event.spontaneous():  # If triggered by the user
            self.video_screen.thread.stop()
            reply = QMessageBox.question(
                self,
                "Quit Application",
                "Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
                )
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            self.data_signal.emit(self.data)
            super().closeEvent(event)

    def update_slider_label_postion(self):
        value = self.slider.value()
        value_str = str(value)
        label_width = max(
            30, 10 * len(value_str)
        )  # Example: base width of 30, plus 10 pixels per character

        self.slider_label.setFixedWidth(label_width)
        slider_width = self.slider.width()
        min_value = self.slider.minimum()
        max_value = self.slider.maximum()
        handle_x = (
            (value - min_value) / (max_value - min_value)
        ) * slider_width
        handle_width_estimate = 15
        label_x = (
            self.slider.x()
            + handle_x
            - (label_width // 2)
            + (handle_width_estimate // 2)
        )
        label_y = (
            self.slider.y() - 25
        )  # Adjust Y as needed to be above the slider

        self.slider_label.move(label_x, label_y)
        self.slider_label.setText(value_str)

    # Step 2: Override the resizeEvent method
    def resizeEvent(self, event):
        self.update_slider_label_postion()
        event.accept()  # Call the base class method to ensure the event is properly handled

    def changeFrame(self, value):
        self.update_slider_label_postion()
        # if self.thread.isRunning:
        #     self.thread.stop()
        self.video_screen.thread.setFrameNumber(
            value
        )  # Pass the slider value to the thread
        self.video_screen.thread.start()

signal.signal(signal.SIGINT, signal.SIG_DFL)


def apply_dark_theme(app):
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(dark_palette)
    app.setStyleSheet("QCheckBox { color: white; }")


def apply_light_theme(app):
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(255, 255, 255))
    light_palette.setColor(QPalette.WindowText, Qt.black)
    light_palette.setColor(QPalette.Base, QColor(240, 240, 240))
    light_palette.setColor(QPalette.AlternateBase, QColor(255, 255, 255))
    light_palette.setColor(QPalette.ToolTipBase, Qt.black)
    light_palette.setColor(QPalette.ToolTipText, Qt.black)
    light_palette.setColor(QPalette.Text, Qt.black)
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ButtonText, Qt.black)
    light_palette.setColor(QPalette.BrightText, Qt.red)
    light_palette.setColor(QPalette.Link, QColor(0, 122, 204))
    light_palette.setColor(QPalette.Highlight, QColor(0, 122, 204))
    light_palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(light_palette)
    app.setStyleSheet("QCheckBox { color: black; }")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow(app)
    window.show()
    print("App is running")
    sys.exit(app.exec())
    print("App is closing")
