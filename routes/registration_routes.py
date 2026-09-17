# routes/registration_routes.py

from flask import Blueprint, request, jsonify, current_app, render_template
from database.queries import add_student
from database.connection import get_db_connection
from modules.face_encoder import get_face_encodings
from modules.camera import VideoCamera
from modules.recognizer import FaceRecognizer
from utils.decorators import login_required
from utils.helpers import validate_mobile
import cv2
import face_recognition
import numpy as np
import time
import logging
import re

logger = logging.getLogger(__name__)

registration_bp = Blueprint('registration', __name__)

MAX_STUDENT_ID_LEN = 10
MAX_NAME_LEN = 100
MAX_FATHER_NAME_LEN = 100
MAX_DEPT_LEN = 50


def validate_inputs(student_id, name, father_name,
                    department, year, semester):
    if len(student_id) > MAX_STUDENT_ID_LEN:
        return False, f"Student ID too long. Max {MAX_STUDENT_ID_LEN} characters."
    if len(name) > MAX_NAME_LEN:
        return False, "Name too long. Max 100 characters."
    if father_name and len(father_name) > MAX_FATHER_NAME_LEN:
        return False, "Father's name too long. Max 100 characters."
    if len(department) > MAX_DEPT_LEN:
        return False, "Department name too long."
    if not re.match(r'^[a-zA-Z0-9_-]+$', student_id):
        return False, "Student ID can only contain letters, numbers, - and _"
    if not re.match(r'^[a-zA-Z\s]+$', name):
        return False, "Name can only contain letters and spaces."
    try:
        year_int = int(year)
        sem_int = int(semester)
        if year_int not in [1, 2, 3]:
            return False, "Year must be 1, 2 or 3."
        if sem_int not in [1, 2, 3, 4, 5, 6]:
            return False, "Semester must be between 1 and 6."
    except ValueError:
        return False, "Year and Semester must be valid numbers."
    return True, None


@registration_bp.route('/registration')
@login_required
def registration_page():
    return render_template('registration.html')


def capture_averaged_encoding(camera, total_attempts=10, delay=0.25):
    """Capture multiple frames and return averaged encoding"""
    encodings = []
    failed = 0

    logger.info(f"Starting capture: {total_attempts} attempts")

    for i in range(total_attempts):
        try:
            frame = camera.get_frame()

            if frame is None:
                failed += 1
                logger.warning(f"Frame {i+1}: Empty frame.")
                time.sleep(delay)
                continue

            img = frame.copy()
            if img.dtype != np.uint8:
                img = img.astype(np.uint8)
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

            # ✅ Convert BGR to RGB directly here
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            rgb = np.ascontiguousarray(rgb, dtype=np.uint8)

            # ✅ Use face_recognition directly — bypass encoder
            locations = face_recognition.face_locations(rgb, model="hog")

            if not locations:
                failed += 1
                logger.warning(f"Frame {i+1}: No face detected.")
                time.sleep(delay)
                continue

            enc = face_recognition.face_encodings(rgb, locations)
            if enc and len(enc) > 0:
                encodings.append(enc[0])
                logger.info(f"Frame {i+1}: Encoding captured.")
            else:
                failed += 1
                logger.warning(f"Frame {i+1}: Encoding failed.")

            time.sleep(delay)

        except Exception as e:
            failed += 1
            logger.error(f"Frame {i+1}: Error: {e}")
            time.sleep(delay)
            continue

    total_captured = len(encodings)
    logger.info(
        f"Capture done: {total_captured} good, "
        f"{failed} failed out of {total_attempts}"
    )

    if total_captured < 5:
        logger.error(
            f"Not enough encodings: {total_captured}. Minimum 5 needed."
        )
        return None, total_captured

    averaged = np.mean(encodings, axis=0)
    logger.info(f"Averaged encoding from {total_captured} frames.")
    return averaged, total_captured


@registration_bp.route('/register_student', methods=['POST'])
@login_required
def register_student():
    try:

        # 1. Extract Form Fields
        student_id  = request.form.get('student_id', '').strip()
        name        = request.form.get('name', '').strip()
        father_name = request.form.get('father_name', '').strip()
        department  = request.form.get('department', '').strip()
        mobile      = request.form.get('mobile_number', '').strip()
        year        = request.form.get('year', '').strip()
        semester    = request.form.get('semester', '').strip()

        # 2. Validate Required Fields
        if not all([student_id, name, department, year, semester]):
            return jsonify({
                "status": "error",
                "message": "Please fill all required fields."
            }), 400

        # 3. Validate Input
        valid, error_msg = validate_inputs(
            student_id, name, father_name,
            department, year, semester
        )
        if not valid:
            return jsonify({
                "status": "error",
                "message": error_msg
            }), 400

        # 4. Validate Mobile
        if mobile and not validate_mobile(mobile):
            return jsonify({
                "status": "error",
                "message": "Invalid mobile number. Must be 10 digits."
            }), 400

        # 5. Check Duplicate
        conn = get_db_connection()
        if conn is None:
            return jsonify({
                "status": "error",
                "message": "Database connection failed."
            }), 500

        try:
            existing = conn.execute(
                "SELECT student_id FROM students WHERE student_id = ?",
                (student_id,)
            ).fetchone()
        finally:
            conn.close()

        if existing:
            return jsonify({
                "status": "error",
                "message": f"Student ID {student_id} already exists."
            }), 409

        # 6. ✅ Stop existing stream and reinitialize camera fresh
        existing_camera = current_app.config.get("CAMERA")
        if existing_camera:
            try:
                existing_camera.stop_camera()
                logger.info("Stopped existing camera stream.")
            except Exception as e:
                logger.warning(f"Could not stop existing camera: {e}")
            current_app.config["CAMERA"] = None

        # ✅ Wait for camera to fully release
        time.sleep(1.5)

        # 7. Initialize fresh camera
        try:
            camera_id = current_app.config.get("CAMERA_ID", 0)
            camera = VideoCamera(camera_id)
            current_app.config["CAMERA"] = camera

            # ✅ Longer warmup — discard first 15 frames
            logger.info("Warming up camera...")
            time.sleep(1.0)
            for _ in range(10):
                camera.get_frame()
                time.sleep(0.1)

            logger.info("Camera ready for capture.")

        except Exception as e:
            logger.error(f"Camera init failed: {e}")
            return jsonify({
                "status": "error",
                "message": "Camera could not be initialized. Check webcam."
            }), 500

        # 8. Capture + Average Frames
        logger.info(f"Starting capture for: {student_id} - {name}")

        averaged_encoding, frames_captured = capture_averaged_encoding(
            camera,
            total_attempts=10,
            delay=0.2
        )

        if averaged_encoding is None:
            return jsonify({
                "status": "error",
                "message": (
                    f"Face capture failed. Only {frames_captured} "
                    f"clear frames (minimum 5 needed).\n\n"
                    f"Please ensure:\n"
                    f"• Face clearly visible in camera\n"
                    f"• Good lighting on face\n"
                    f"• Look straight at camera\n"
                    f"• Remove mask or dark glasses"
                )
            }), 400

        # 9. Save to Database
        success = add_student(
            student_id=student_id,
            name=name,
            father_name=father_name,
            department=department,
            mobile=mobile,
            year=int(year),
            semester=int(semester),
            encoding=averaged_encoding
        )

        if not success:
            return jsonify({
                "status": "error",
                "message": "Failed to save student."
            }), 500

        # 10. Update Cache
        try:
            recognizer = current_app.config.get("RECOGNIZER")
            if recognizer is None:
                recognizer = FaceRecognizer()
                current_app.config["RECOGNIZER"] = recognizer
            recognizer.add_to_cache(student_id, name, averaged_encoding)
        except Exception as e:
            logger.warning(f"Cache update failed (non-critical): {e}")

        logger.info(
            f"Student registered: {student_id} - {name} "
            f"({frames_captured} frames)"
        )

        return jsonify({
            "status": "success",
            "message": (
                f"✅ {name} registered successfully!\n"
                f"Face captured from {frames_captured} frames."
            )
        }), 200

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            "status": "error",
            "message": "Unexpected error. Please try again."
        }), 500