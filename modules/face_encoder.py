# modules/face_encoder.py

import face_recognition
import cv2
import numpy as np
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def _safe_to_rgb(frame, max_width=640):
    
    try:
        if frame is None:
            return None

        img = frame.copy()

        if img.dtype != np.uint8:
            img = img.astype(np.uint8)

        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif len(img.shape) == 3 and img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        
        h, w = img.shape[:2]
        if w > max_width:
            scale = max_width / w
            new_w = int(w * scale)
            new_h = int(h * scale)
            img = cv2.resize(
                img, (new_w, new_h),
                interpolation=cv2.INTER_AREA
            )

        # Convert BGR to RGB
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Force contiguous
        rgb = np.ascontiguousarray(rgb, dtype=np.uint8)

        return rgb

    except Exception as e:
        logger.error(f"Frame conversion error: {e}")
        return None


def get_face_encodings(image_path=None, frame=None,
                       model="hog", resize_width=640):
    """Single face encoding — used during registration."""
    try:
        if image_path:
            image = face_recognition.load_image_file(image_path)
            # Resize if too large
            h, w = image.shape[:2]
            if w > resize_width:
                scale = resize_width / w
                image = cv2.resize(
                    image,
                    (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_AREA
                )
            image = np.ascontiguousarray(image, dtype=np.uint8)

        elif frame is not None:
            image = _safe_to_rgb(frame, max_width=resize_width)
            if image is None:
                logger.error("Frame conversion failed.")
                return None
        else:
            logger.error("No image source provided.")
            return None

        if image is None or image.size == 0:
            logger.warning("Empty image.")
            return None

        if image.ndim != 3 or image.shape[2] != 3:
            logger.error(f"Wrong shape: {image.shape}")
            return None

        logger.info(
            f"Processing image: {image.shape} dtype={image.dtype}"
        )

        face_locations = face_recognition.face_locations(
            image, model=model
        )

        if len(face_locations) == 0:
            logger.info("No face detected.")
            return None

        if len(face_locations) > 1:
            logger.warning("Multiple faces. Using first.")

        encodings = face_recognition.face_encodings(
            image, face_locations
        )

        if encodings is not None and len(encodings) > 0:
            return encodings[0]

        return None

    except Exception as e:
        logger.error(f"Face encoding error: {e}")
        return None


def get_all_face_encodings(frame, resize_width=640):
    """
    Returns ALL face encodings found in frame.
    Used for multi-student simultaneous attendance.
    """
    try:
        if frame is None:
            return []

        rgb_frame = _safe_to_rgb(frame, max_width=resize_width)

        if rgb_frame is None:
            logger.warning("Frame conversion failed.")
            return []

        if rgb_frame.ndim != 3 or rgb_frame.shape[2] != 3:
            logger.error(f"Wrong shape: {rgb_frame.shape}")
            return []

        face_locations = face_recognition.face_locations(
            rgb_frame, model="hog"
        )

        if not face_locations:
            return []

        encodings = face_recognition.face_encodings(
            rgb_frame, face_locations
        )

        if encodings:
            logger.info(f"Detected {len(encodings)} face(s).")

        return encodings

    except Exception as e:
        logger.error(f"Multi-face encoding error: {e}")
        return []


def compare_faces(known_encoding, face_encoding_to_check,
                  tolerance=0.45):
    """Compare two faces."""
    try:
        distances = face_recognition.face_distance(
            [known_encoding], face_encoding_to_check
        )
        match = distances[0] <= tolerance
        return match, float(distances[0])

    except Exception as e:
        logger.error(f"Face comparison error: {e}")
        return False, None