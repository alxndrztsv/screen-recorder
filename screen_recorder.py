import argparse
import os
import sys
import time

import cv2
import numpy as np
import pyautogui
from mss import mss
from pynput import keyboard


# --- Type hints for key objects from pynput ---
KeyType = keyboard.Key | keyboard.KeyCode | None

# --- State variable for the keyboard listener ---
stop_recording = False


def setup_arguments() -> argparse.Namespace:
    """Configure command-line arguments."""
    parser = argparse.ArgumentParser(description="Screen recorder with custom cursor")
    parser.add_argument(
        "-m", "--monitor", type=int, default=1,
        help="Monitor index to record (1 = primary, 2 = secondary, etc.)"
    )
    parser.add_argument(
        "-f", "--fps", type=float, default=30.0,
        help="Frames per second for the output video"
    )
    parser.add_argument(
        "-c", "--cursor", type=str, default="cursor.png",
        help="Path to the custom cursor.png file (with transparency)"
    )
    parser.add_argument(
        "-o", "--output", type=str, default="screen_record.mp4",
        help="Output video file name (e.g., recording.mp4 or recording.avi)"
    )
    parser.add_argument(
        "-s", "--size", type=int, default=32,
        help="Size (width and height) to resize the cursor to"
    )
    parser.add_argument(
        "--no-cursor",
        action="store_true",
        help="Do not show any cursor in the recording."
    )
    return parser.parse_args()


def get_codec(filename: str) -> int:
    """Determine video codec from file extension."""
    if filename.endswith(".mp4"):
        return cv2.VideoWriter_fourcc(*"mp4v")  # .mp4
    return cv2.VideoWriter_fourcc(*"XVID")      # .avi


def on_press(key: KeyType) -> bool | None:
    """Stop recording when F5 is pressed."""
    global stop_recording
    try:
        if key == keyboard.Key.f5:
            stop_recording = True
            return False  # stop the listener
    except Exception as e:
        print(f"Key listener error: {e}")


# --- Start keyboard listener in the background ---
listener = keyboard.Listener(on_press=on_press)
listener.start()


def overlay_image_alpha(screen: np.ndarray, cursor: np.ndarray, x: int, y: int) -> None:
    """
    Overlay a cursor image (with alpha) onto a screen capture.

    Args:
        screen: The background image (BGR format).
        cursor: The foreground cursor image (BGRA format).
        x: The x-coordinate for the top-left corner of the cursor.
        y: The y-coordinate for the top-left corner of the cursor.

    Returns:
        None
    """
    screen_h, screen_w = screen.shape[:2]
    cursor_h, cursor_w = cursor.shape[:2]

    # --- Calculate boundary coordinates of the screen where to draw cursor rectangle box ---
    # Top-left corner coordinate of the cursor boundary box
    cur_box_x1 = max(0, x)  # do not go left the screen
    cur_box_y1 = max(0, y)  # do not go above the screen
    # Bottom-right corner coordinate of the cursor boundary box
    cur_box_x2 = min(screen_w, x + cursor_w)  # do not go right the screen
    cur_box_y2 = min(screen_h, y + cursor_h)  # do not go under the screen

    # Width and height of the box where cursor will be drawn
    cur_box_w = cur_box_x2 - cur_box_x1
    cur_box_h = cur_box_y2 - cur_box_y1

    # Do nothing if the cursor is completely off-screen (e.g. monitor 2)
    if cur_box_w <= 0 or cur_box_h <= 0:
        return

    # --- Calculate portion of cursor image which will be drawn in cursor rectangle box ---
    # Top-left corner on cursor image
    cur_img_x1 = max(0, -x)
    cur_img_y1 = max(0, -y)
    # Bottom-right corner on cursor image
    cur_img_x2 = cur_img_x1 + cur_box_w
    cur_img_y2 = cur_img_y1 + cur_box_h

    # --- Perform blending ---
    try:
        # Get the relevant regions of interest
        cursor_roi = cursor[cur_img_y1:cur_img_y2, cur_img_x1:cur_img_x2]
        screen_roi = screen[cur_box_y1:cur_box_y2, cur_box_x1:cur_box_x2]

        # Get RGB and alpha channels from cursor
        cursor_rgb = cursor_roi[..., :3]
        alpha_mask = cursor_roi[..., 3] / 255.0
        # Make alpha_mask 3D for broadcasting
        alpha_mask = np.dstack([alpha_mask] * 3)

        # Blend the two images
        blended_roi = (1.0 - alpha_mask) * screen_roi + alpha_mask * cursor_rgb

        # Place the blended region back onto the main screen
        screen[cur_box_y1:cur_box_y2, cur_box_x1:cur_box_x2] = blended_roi.astype(np.uint8)
            
    except Exception as e:
        print(f"Error during overlay: {e}")
        print(f"Coords: x={x}, y={y} | Cursor box: {cur_box_y1}:{cur_box_y2}, {cur_box_x1}:{cur_box_x2} | Cursor img: {cur_img_y1}:{cur_img_y2}, {cur_img_x1}:{cur_img_x2}")


def main() -> None:
    """Main function to run the screen recorder."""
    args = setup_arguments()
    cursor_img = None
    
    # --- Load custom cursor ---
    cursor_path = args.cursor

    if os.path.exists(cursor_path):
        try:
            cursor_img = cv2.imread(args.cursor, cv2.IMREAD_UNCHANGED)
            if cursor_img is None:
                raise FileNotFoundError
            # Resize cursor
            cursor_img = cv2.resize(
                cursor_img, (args.size, args.size), interpolation=cv2.INTER_AREA
            )
        except FileNotFoundError:
            print(f"Error: Could not load '{args.cursor}'. Make sure it's a valid image file.")
            sys.exit(1)
    else:
        # If the *default* 'cursor.png' is missing, record without cursor overlay.
        print("Info: Default 'cursor.png' not found. Recording without a cursor.")

    # --- Setup screen capture ---
    with mss() as sct:
        try:
            # sct.monitors[0] is all monitors, [1] is primary, etc.
            if args.monitor < 0 or args.monitor >= len(sct.monitors):
                print(f"Error: Invalid monitor index {args.monitor}.")
                print(f"Available monitors: 1 to {len(sct.monitors) - 1}")
                sys.exit(1)
            
            monitor = sct.monitors[args.monitor]
            
            # *** DYNAMIC RESOLUTION ***
            # Use the monitor's actual width and height
            resolution = (monitor["width"], monitor["height"])
            
            # Store monitor's top-left corner for coordinate conversion
            monitor_left = monitor["left"]
            monitor_top = monitor["top"]

        except Exception as e:
            print(f"Error setting up monitor: {e}")
            sct.close()
            sys.exit(1)

        # --- Setup video writer ---
        codec = get_codec(args.output)
        out = cv2.VideoWriter(args.output, codec, args.fps, resolution)

        # --- Setup preview window ---
        cv2.namedWindow("Live", cv2.WINDOW_NORMAL)
        # Resize preview window to a fraction of the resolution
        preview_width = resolution[0] // 4
        preview_height = resolution[1] // 4
        cv2.resizeWindow("Live", preview_width, preview_height)
        
        # --- Main Loop ---
        print(f"Recording monitor {args.monitor} ({resolution[0]}x{resolution[1]}) to {args.output} at {args.fps} fps.")
        print("Press 'F5' to stop.")
        
        # For frame rate limiting
        frame_time = 1.0 / args.fps
        
        try:
            while True:
                loop_start_time = time.time()

                # Capture the screen
                frame = np.array(sct.grab(monitor))
                # Convert BGRA (from mss) to BGR (for VideoWriter)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

                # --- Conditionally overlay the cursor ---
                if cursor_img is not None:
                    # Get cursor mouse position
                    cursor_x, cursor_y = pyautogui.position()

                    # Convert to monitor-relative coordinates
                    frame_x = cursor_x - monitor_left
                    frame_y = cursor_y - monitor_top

                    # Overlay custom cursor
                    # We pass the BGRA frame for overlaying, but write the BGR frame
                    overlay_image_alpha(frame_bgr, cursor_img, frame_x, frame_y)

                # Write frame
                out.write(frame_bgr)

                # Show preview
                cv2.imshow("Live", frame_bgr)

                if (cv2.waitKey(1) & 0xFF == ord('q') or stop_recording or cv2.getWindowProperty("Live", cv2.WND_PROP_VISIBLE) < 1):
                    break

                # *** FRAME RATE LIMITING ***
                elapsed_time = time.time() - loop_start_time
                sleep_time = frame_time - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\nRecording stopped by user.")
        finally:
            # Release resources
            print("Cleaning up and saving video...")
            out.release()
            cv2.destroyAllWindows()
            listener.stop()
            print(f"Video saved to '{args.output}'")


if __name__ == "__main__":
    main()