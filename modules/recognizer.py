# modules/recognizer.py

import face_recognition
import numpy as np
import logging
from config import Config
from database.connection import get_db_connection
from threading import Lock

logger = logging.getLogger(__name__)


class FaceRecognizer:

    def __init__(self):
        self.known_encodings = []
        self.known_ids = []
        self.known_names = []
        self.cache_loaded = False
        self.lock = Lock()

    # --------------------------------------------------
    # Load Encodings into Memory Cache
    # --------------------------------------------------
    def load_encodings(self, force_reload=False):
        """Load all student encodings from DB into memory"""

        if self.cache_loaded and not force_reload:
            return

        conn = get_db_connection()
        if not conn:
            logger.error("Cannot load encodings: DB connection failed.")
            return

        try:
            cursor = conn.cursor()
            students = cursor.execute(
                "SELECT student_id, name, face_encoding FROM students "
                "WHERE COALESCE(is_active, 1) = 1"
            ).fetchall()

            temp_encodings = []
            temp_ids = []
            temp_names = []
            failed = 0

            for student in students:
                try:
                    if student['face_encoding']:
                        # ✅ Use numpy instead of pickle — safe deserialization
                        encoding = np.frombuffer(
                            student['face_encoding'],
                            dtype=np.float64
                        )
                        temp_encodings.append(encoding)
                        temp_ids.append(student['student_id'])
                        temp_names.append(student['name'])
                except Exception as e:
                    failed += 1
                    logger.warning(
                        f"Failed to load encoding for "
                        f"{student['student_id']}: {e}"
                    )

            # ✅ Lock only when updating cache — not during DB query
            with self.lock:
                self.known_encodings = temp_encodings
                self.known_ids = temp_ids
                self.known_names = temp_names
                self.cache_loaded = True

            logger.info(
                f"Encoding cache loaded: {len(temp_encodings)} students "
                f"({failed} failed) out of {len(students)} total."
            )

        except Exception as e:
            logger.error(f"Encoding load error: {e}")
        finally:
            conn.close()

    # --------------------------------------------------
    # Force Reload Cache
    # --------------------------------------------------
    def reload_encodings(self):
        """Force reload cache — call after new student registered"""
        logger.info("Force reloading encoding cache...")
        self.cache_loaded = False
        self.load_encodings(force_reload=True)
        logger.info(
            f"Cache refreshed: {len(self.known_encodings)} students loaded."
        )

    # --------------------------------------------------
    # Add Single Encoding to Cache
    # --------------------------------------------------
    def add_to_cache(self, student_id, name, encoding):
        """Add a single new student to cache without full reload"""
        with self.lock:
            self.known_encodings.append(encoding)
            self.known_ids.append(student_id)
            self.known_names.append(name)
            logger.info(
                f"Added {student_id} - {name} to encoding cache. "
                f"Total: {len(self.known_encodings)}"
            )

    # --------------------------------------------------
    # Identify Single Face
    # --------------------------------------------------
    def identify_face(self, encoding):
        """Compare single encoding against cached encodings"""

        if not self.cache_loaded:
            self.load_encodings()

        if not self.known_encodings:
            logger.warning("No encodings in cache. Cannot identify face.")
            return None, "Unknown", 0

        try:
            known_array = np.array(self.known_encodings)

            matches = face_recognition.compare_faces(
                known_array,
                encoding,
                tolerance=Config.FACE_MATCH_TOLERANCE
            )

            distances = face_recognition.face_distance(
                known_array,
                encoding
            )

            best_index = int(np.argmin(distances))

            if bool(matches[best_index]):
                confidence = round(
                    (1 - float(distances[best_index])) * 100, 2
                )
                logger.info(
                    f"Face identified: {self.known_ids[best_index]} - "
                    f"{self.known_names[best_index]} "
                    f"({confidence}% confidence)"
                )
                return (
                    self.known_ids[best_index],
                    self.known_names[best_index],
                    confidence
                )

            logger.info(
                f"Face not recognized. "
                f"Closest distance: {float(distances[best_index]):.3f}"
            )
            return None, "Unknown", 0

        except Exception as e:
            logger.error(f"Face identification error: {e}")
            return None, "Unknown", 0

    # --------------------------------------------------
    # ✅ Identify ALL Faces Simultaneously
    # --------------------------------------------------
    def identify_all_faces(self, encodings):
        """
        Identify multiple faces from a single frame simultaneously.
        Returns list of results for each face found.
        """
        if not self.cache_loaded:
            self.load_encodings()

        if not self.known_encodings:
            logger.warning("No encodings in cache.")
            return []

        if not encodings:
            return []

        results = []

        try:
            # ✅ Convert to numpy array once for all comparisons
            known_array = np.array(self.known_encodings)

            for encoding in encodings:
                try:
                    matches = face_recognition.compare_faces(
                        known_array,
                        encoding,
                        tolerance=Config.FACE_MATCH_TOLERANCE
                    )

                    distances = face_recognition.face_distance(
                        known_array,
                        encoding
                    )

                    best_index = int(np.argmin(distances))

                    if bool(matches[best_index]):
                        confidence = round(
                            (1 - float(distances[best_index])) * 100, 2
                        )
                        results.append({
                            "student_id": self.known_ids[best_index],
                            "name": self.known_names[best_index],
                            "confidence": confidence,
                            "identified": True
                        })
                        logger.info(
                            f"Identified: {self.known_ids[best_index]} - "
                            f"{self.known_names[best_index]} "
                            f"({confidence}%)"
                        )
                    else:
                        results.append({
                            "student_id": None,
                            "name": "Unknown",
                            "confidence": 0,
                            "identified": False
                        })

                except Exception as e:
                    logger.error(f"Single face identification error: {e}")
                    results.append({
                        "student_id": None,
                        "name": "Unknown",
                        "confidence": 0,
                        "identified": False
                    })
                    continue

        except Exception as e:
            logger.error(f"Multi-face identification error: {e}")

        logger.info(
            f"Multi-face result: {len(results)} faces processed, "
            f"{sum(1 for r in results if r['identified'])} identified."
        )

        return results

    # --------------------------------------------------
    # Cache Status
    # --------------------------------------------------
    def get_cache_status(self):
        """Return current cache info"""
        return {
            "loaded": self.cache_loaded,
            "total_students": len(self.known_encodings)
        }