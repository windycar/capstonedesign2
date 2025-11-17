# camera.py
import cv2
import threading
import time
from picamera2 import Picamera2

class Camera:
    def __init__(self, preview_w=800, preview_h=450, fps=24):
        """Initialize camera using picamera2."""
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (preview_w, preview_h)},
            controls={"FrameRate": fps}
        )
        self.picam2.configure(config)
        
        self.frame = None
        self.stopped = False
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        
        print("[INFO] picamera2 initialized.")

    def _capture_loop(self):
        """Internal thread loop to continuously grab frames."""
        print("[INFO] Camera capture thread started.")
        self.picam2.start()
        
        while not self.stopped:
            frame = self.picam2.capture_array()
            with self.lock:
                self.frame = frame
        
        self.picam2.stop()
        print("[INFO] Camera capture thread stopped.")

    def start(self):
        """Start the capture thread."""
        self.stopped = False
        self.thread.start()

    def read(self):
        """Read the latest frame from the thread."""
        with self.lock:
            if self.frame is not None:
                # picamera2 captures in RGB, OpenCV/YOLO expects BGR
                return cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
            return None

    def stop(self):
        """Stop the capture thread."""
        self.stopped = True
        if self.thread.is_alive():
            self.thread.join()