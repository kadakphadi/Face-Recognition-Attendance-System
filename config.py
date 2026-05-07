# config.py

import os
import warnings
import secrets
from dotenv import load_dotenv

# Load environment variables from .env (if present)
load_dotenv()

class Config:
    """Central configuration file for the Face Attendance System"""

    # ---------------------------
    # Base Paths
    # ---------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
    DATABASE_PATH = os.path.join(INSTANCE_DIR, "attendance_system.db")
    LOG_DIR = os.path.join(BASE_DIR, "logs")

    # ---------------------------
    # Flask Core Settings
    # ---------------------------
    _secret = os.environ.get("SECRET_KEY")
    if _secret:
        SECRET_KEY = _secret
    else:
        # ✅ Generate a random secure key as fallback
        # Still warns but at least not predictable
        SECRET_KEY = secrets.token_hex(32)
        warnings.warn(
            "WARNING: SECRET_KEY environment variable not set. "
            "Using a randomly generated key. "
            "Sessions will reset on every server restart. "
            "Set SECRET_KEY in production!",
            stacklevel=2
        )

    SESSION_PERMANENT = False
    # ✅ Protect session cookie from JavaScript access (XSS mitigation)
    SESSION_COOKIE_HTTPONLY = True
    # ✅ Prevent session cookie from being sent on cross-site requests (CSRF)
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ---------------------------
    # Face Recognition Settings
    # ---------------------------
    FACE_MATCH_TOLERANCE = float(os.environ.get("FACE_TOLERANCE", 0.45))
    CAMERA_ID = int(os.environ.get("CAMERA_ID", 0))

    # ---------------------------
    # Upload Limit
    # ---------------------------
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


def init_directories():
    """
    Create required directories.
    ✅ Called explicitly from app.py — not at import time.
    """
    dirs = [
        Config.INSTANCE_DIR,
        Config.LOG_DIR,
    ]
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)