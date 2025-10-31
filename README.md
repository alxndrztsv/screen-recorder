# Custom Cursor Screen Recorder

A Python-based screen recording utility that allows you to overlay a custom image as the mouse cursor. Perfect for creating tutorials, software demonstrations, and presentations where a more visible and stylized cursor is needed.

![Demo GIF of the recorder in action](https-placeholder-for-your-demo.gif)

## Features

-   **Custom Cursor:** Overlays a transparent PNG image as the mouse cursor in the final recording.
-   **Multi-Monitor Support:** Select any specific monitor to record.
-   **Configurable:** Adjust FPS, output filename, video format (`.mp4` or `.avi`), and cursor size via command-line arguments.
-   **Live Preview:** Shows a real-time preview of what's being recorded.
-   **Simple Controls:** Press the `F5` key to stop the recording at any time.
-   **Frame Rate Limiting:** Ensures a smooth and consistent video output at the desired frame rate.

## Prerequisites

This script requires Python 3. You will also need to install the following libraries:

-   `opencv-python`
-   `numpy`
-   `pyautogui`
-   `mss`
-   `pynput`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://your-repository-url/custom-cursor-screen-recorder.git
    cd custom-cursor-screen-recorder
    ```

2.  **Install the required packages:**
    ```bash
    pip install opencv-python numpy pyautogui mss pynput
    ```

3.  **Add a cursor image:**
    Place your custom cursor image, preferably a PNG with a transparent background, in the project directory and name it `cursor.png`, or specify a different path using the `-c` argument.

## Usage

Run the script from your terminal. The recording will start immediately and a live preview window will appear. Press **F5** to stop the recording and save the file.

**Basic Command:**
```bash
python screen_recorder.py
```

### Command-Line Arguments

You can customize the recording using the following arguments:

| Argument          | Short | Description                                                   | Default              |
| ----------------- | ----- | ------------------------------------------------------------- | -------------------- |
| `--monitor`       | `-m`  | The monitor index to record (1 = primary, 2 = secondary...).  | `1`                  |
| `--fps`           | `-f`  | Frames per second for the output video.                       | `30.0`               |
| `--cursor`        | `-c`  | Path to the custom cursor image (with transparency).          | `cursor.png`         |
| `--output`        | `-o`  | Output video file name (e.g., `recording.mp4` or `rec.avi`).  | `screen_record.mp4`  |
| `--size`          | `-s`  | The size (width & height) to resize the cursor image to.      | `32`                 |
| `--no-cursor`     |       | A flag to disable the custom cursor overlay.                  | Not set              |

**Example:** Record the secondary monitor at 60 FPS and save it as `tutorial.mp4`:
```bash
python screen_recorder.py -m 2 -f 60.0 -o tutorial.mp4
```

---

## How It Works

The script integrates several libraries to handle screen capture, user input, and video processing in a continuous loop.

1.  **Configuration:** The `argparse` library reads command-line arguments to set up the recording parameters.

2.  **Keyboard Listener:** A non-blocking keyboard listener from `pynput` runs in a background thread, waiting for the `F5` key to be pressed to gracefully stop the recording.

3.  **Screen Capture:** The `mss` library is used for high-performance screen capturing. It grabs the screen of the specified monitor.

4.  **Video Writing:** OpenCV (`cv2`) is used to initialize a `VideoWriter` object, which takes image frames and encodes them into the final video file. The codec is automatically determined by the output file extension.

5.  **Main Recording Loop:** The core of the application runs a `while` loop that performs the following on each iteration:
    * **Captures** a screenshot of the monitor.
    * **Gets** the current mouse coordinates using `pyautogui`.
    * **Overlays** the custom cursor image onto the captured frame at the mouse's position.
    * **Writes** the modified frame to the video file.
    * **Displays** the frame in a live preview window.
    * **Pauses** briefly to maintain the target frame rate.

### The Alpha Blending Process

The custom cursor is drawn onto each frame using a technique called **alpha blending**. This ensures that the transparent parts of the cursor image let the background screen content show through.



The process works as follows:
1.  **Isolate the Alpha Channel:** The script takes the cursor image, which is in BGRA format (Blue, Green, Red, Alpha), and extracts its alpha channel. The alpha value of a pixel determines its transparency (0 = fully transparent, 255 = fully opaque).
2.  **Create a Mask:** The alpha channel is normalized to a range of `0.0` to `1.0` to be used as a blending mask.
3.  **Blend Pixels:** For each pixel where the cursor overlaps the screen capture, a new pixel value is calculated using the formula:

    $$
    \text{Final Pixel} = (1 - \alpha) \times \text{Screen Pixel} + \alpha \times \text{Cursor Pixel}
    $$

    This calculation is performed for each of the Blue, Green, and Red channels, resulting in a seamless blend of the cursor onto the background.

4.  **Update the Frame:** The newly blended region is placed back onto the screen capture before it is written to the video file.

This process is repeated for every frame, making it appear as if the custom cursor is moving naturally across the screen in the final video.

## License

This project has no license. No idea for this is for.
