# <p style="text-align: center;">Scenes Information Recorder for Film Editors</p>

<p align="center">
  <img src="resources/images/title_logo.jpeg" alt="Title Logo" width="400"/>
</p>

<p style="text-align: center;"><strong>Project under development.</strong></p>

This project is designed to make work easier for film production or post-production editors. The program is intended to read frames from the film and collect relevant information about the scenes, such as:

- Information about the VFX effect to be added to the scene,
- Information about the ADR effect to be added to the scene,
- The time range of the entire scene (from the beginning of the movie) in which the VFX appears,
- Actual time range within the scene (from the beginning of the movie) during which the ADR effect occurs.
- The actual time range of the entire scene in which VFX appears,
- The time range within the scene during which the ADR effect occurs,

After reviewing the entire movie, an Excel file is generated, with a summary of the processed information, and thumbnails of the scenes in which VFX effects occur.

<div align="center">

![GitHub issues](https://img.shields.io/github/issues-raw/PiotrWeppo/Scenes-information-recorder-for-video-editors)
![GitHub last commit](https://img.shields.io/github/last-commit/PiotrWeppo/Scenes-information-recorder-for-video-editors)
![GitHub](https://img.shields.io/github/license/PiotrWeppo/Scenes-information-recorder-for-video-editors)

[Getting started](#getting-started) •
[Usage](#usage) •
[Behind the Scenes](#behind-the-scenes) •
[License](#license)

</div>

## Installation

---

**1. Clone the repository:**

      git clone https://github.com/PiotrWeppo/Scenes_Information_Recorder.git
      cd Scenes_Information_Recorder

**1. Set up a virtual environment:**

      python -m venv venv

**2. Activate the virtual environment:**

- On Windows:

      .\venv\Scripts\activate

- On macOS and Linux:

      source venv/bin/activate

**3. Install necessary libraries:**

      pip install -r requirements.txt

## Usage

---

The program uses the GUI to help select the initial parameters of the video, such as source and file path, but especially the first frame from which to check the video (some videos may start with a title card, which should be separated from the video being processed) and the areas of text searched by the OCR engine.

<p align="center">
      <img src="images/gui_usage.gif" alt="GUI Presentation Example">
      <br>Showcasing GUI part of application.
      <br><img src="images/cli.gif" alt="CLI Presentation Example" width="80%">
      <br>Showcasing CLI part of application.
</p>

## Behind the Scenes

---

The graphic below shows a simplified diagram of the program's processes.

<p align="center"> <img src="images/graph.svg" alt="Graph"/> </p>

## License

---

Copyright © 2024 Piotr Weppo

This project is [MIT](https://choosealicense.com/licenses/mit/) licenced.
