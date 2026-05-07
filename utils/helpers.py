# utils/helpers.py

import os
import cv2
import glob
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def format_date(date_obj=None):
    """Return date in YYYY-MM-DD format"""
    date_obj = date_obj or datetime.now()
    return date_obj.strftime("%Y-%m-%d")


def format_time(time_obj=None):
    """Return time in HH:MM:SS format"""
    time_obj = time_obj or datetime.now()
    return time_obj.strftime("%H:%M:%S")


def save_debug_image(frame, folder="debug", max_images=50):
    """
    Save camera frame for debugging.
    ✅ Limits max images to prevent disk fill up.
    """
    os.makedirs(folder, exist_ok=True)

    # ✅ Cleanup old debug images if over limit
    existing = sorted(glob.glob(os.path.join(folder, "capture_*.jpg")))
    while len(existing) >= max_images:
        try:
            os.remove(existing[0])
            existing.pop(0)
        except Exception as e:
            logger.warning(f"Could not delete old debug image: {e}")
            break

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"capture_{timestamp}.jpg"
    path = os.path.join(folder, filename)

    try:
        cv2.imwrite(path, frame)
        logger.info(f"Debug image saved: {path}")
        return path
    except Exception as e:
        # ✅ logger instead of print
        logger.error(f"Debug image save error: {e}")
        return None


def validate_mobile(mobile):
    """
    Validate Indian-style mobile number:
    - 10 digits
    - starts with 6/7/8/9
    """
    mobile = str(mobile).strip()
    return (
        mobile.isdigit() and
        len(mobile) == 10 and
        mobile[0] in "6789"
    )