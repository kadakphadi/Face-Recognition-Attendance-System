# modules/camera.py

import cv2
import sys
import numpy as np
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class VideoCamera:
    def __init__(self, camera_id=0):
        """Initialize camera with correct backend per platform"""

        if sys.platform == "win32":
            self.video = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        else:
            self.video = cv2.VideoCapture(camera_id)

        # ✅ Force 640x480 resolution
        # 1920x1080 causes dlib/face_recognition to fail on Windows
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.lock = Lock()

        if not self.video.isOpened():
            logger.error(
                "Camera could not be opened. Check webcam connection."
            )
            raise RuntimeError(
                "Camera could not be opened. Check webcam connection."
            )

        # ✅ Log actual resolution
        actual_w = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        logger.info(
            f"Camera {camera_id} initialized: "
            f"{int(actual_w)}x{int(actual_h)}"
        )

    def get_frame(self):
        """Raw frame return karega"""
        with self.lock:
            success, frame = self.video.read()

            if not success or frame is None:
                logger.warning("Failed to read frame from camera.")
                return None

            # ✅ Ensure contiguous uint8 array
            return np.ascontiguousarray(frame, dtype=np.uint8)

    def get_encoded_frame(self):
        """JPEG bytes return karega (browser streaming ke liye)"""
        frame = self.get_frame()
        if frame is None:
            return None

        success, jpeg = cv2.imencode('.jpg', frame)
        if not success:
            logger.warning("Failed to encode frame as JPEG.")
            return None

        return jpeg.tobytes()

    def stop_camera(self):
        """Manual camera release"""
        with self.lock:
            if self.video.isOpened():
                self.video.release()
                logger.info("Camera released successfully.")

    def is_open(self):
        """Camera status check"""
        return self.video.isOpened()
