# routes/attendance_routes.py

from flask import Blueprint, Response, current_app, render_template
from modules.camera import VideoCamera
from modules.face_encoder import get_all_face_encodings
from modules.recognizer import FaceRecognizer
from modules.attendance_marker import AttendanceMarker
from utils.decorators import login_required
import cv2
import logging
import time

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)
marker = AttendanceMarker()


def get_recognizer(app):
    recognizer = app.config.get("RECOGNIZER")
    if recognizer is None:
        recognizer = FaceRecognizer()
        recognizer.load_encodings()
        app.config["RECOGNIZER"] = recognizer
        logger.info("Recognizer initialized and cache loaded.")
    elif not recognizer.cache_loaded:
        recognizer.load_encodings()
    return recognizer


def gen_attendance_stream(camera, app):
    """Generate MJPEG stream with multi-face recognition overlay"""

    with app.app_context():

        frame_count = 0
        recognizer = get_recognizer(app)

        status = recognizer.get_cache_status()
        logger.info(
            f"Attendance stream started. "
            f"Cache: {status['total_students']} students loaded."
        )

        # ✅ Persist last recognition results between frames
        last_results = []
        empty_frame_count = 0
        MAX_EMPTY_FRAMES = 30

        while True:
            frame = camera.get_frame()

            if frame is None:
                empty_frame_count += 1
                logger.warning(
                    f"Empty frame {empty_frame_count}/{MAX_EMPTY_FRAMES}"
                )
                if empty_frame_count >= MAX_EMPTY_FRAMES:
                    logger.error("Camera disconnected — stopping stream.")
                    break
                time.sleep(0.1)
                continue

            empty_frame_count = 0
            frame_count += 1

            # ✅ Process every 3rd frame
            if frame_count % 3 == 0:
                all_encodings = get_all_face_encodings(frame=frame)

                if all_encodings:
                    results = recognizer.identify_all_faces(all_encodings)
                    last_results = results  # ✅ Save results

                    for result in results:
                        if result['identified']:
                            marker.process_recognition(
                                result['student_id'],
                                result['name']
                            )
                else:
                    # ✅ Clear results when no face detected
                    last_results = []

            # ✅ Always draw last known results on every frame
            if last_results:
                for i, result in enumerate(last_results):
                    y_position = 40 + (i * 50)

                    if result['identified']:
                        name = result['name']
                        confidence = result['confidence']

                        # ✅ Green text for recognized face
                        cv2.putText(
                            frame,
                            f"{name} ({confidence}%)",
                            (10, y_position),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2
                        )
                        cv2.putText(
                            frame,
                            "Attendance Marked",
                            (10, y_position + 22),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (0, 220, 0),
                            1
                        )

                    else:
                        # ✅ Red text for unknown face
                        cv2.putText(
                            frame,
                            "Unknown Face",
                            (10, y_position),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 0, 255),
                            2
                        )

                # ✅ Face count at bottom
                identified = sum(
                    1 for r in last_results if r['identified']
                )
                cv2.putText(
                    frame,
                    f"Faces: {len(last_results)} | "
                    f"Identified: {identified}",
                    (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 0),
                    2
                )

            else:
                # ✅ Show scanning message when no face
                cv2.putText(
                    frame,
                    "Scanning for faces...",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (200, 200, 200),
                    2
                )

            # Encode frame as JPEG
            success, jpeg = cv2.imencode('.jpg', frame)
            if not success:
                continue

            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                jpeg.tobytes() +
                b'\r\n'
            )


@attendance_bp.route('/attendance')
@login_required
def attendance_page():
    return render_template('attendance.html')


@attendance_bp.route('/video_feed')
@login_required
def video_feed():
    app = current_app._get_current_object()
    camera = app.config.get("CAMERA")

    if camera is None or not camera.is_open():
        try:
            camera_id = app.config.get("CAMERA_ID", 0)
            camera = VideoCamera(camera_id)
            app.config["CAMERA"] = camera

            # ✅ Single test-read to verify camera is ready
            camera.get_frame()

            logger.info("Camera initialized for attendance.")

        except Exception as e:
            logger.error(f"Camera init failed: {e}")
            return Response(
                b'',
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )

    return Response(
        gen_attendance_stream(camera, app),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@attendance_bp.route('/stop_camera', methods=['GET', 'POST'])
@login_required
def stop_camera():
    camera = current_app.config.get("CAMERA")
    if camera:
        camera.stop_camera()
        current_app.config["CAMERA"] = None
        logger.info("Camera stopped and released.")
    return '', 204