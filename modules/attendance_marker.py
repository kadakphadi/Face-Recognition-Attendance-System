# modules/attendance_marker.py

from datetime import datetime
from threading import Lock
from database.queries import mark_attendance, is_holiday
import logging

logger = logging.getLogger(__name__)


class AttendanceMarker:

    def __init__(self):
        self.marked_today = set()
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.lock = Lock()

    def _load_todays_marked(self, today_date):
        """
        ✅ Load already marked students from DB on date change
        or first run. Prevents duplicate marking after restart.
        """
        from database.connection import get_db_connection
        conn = get_db_connection()
        if not conn:
            return

        try:
            rows = conn.execute(
                "SELECT student_id FROM attendance WHERE date = ?",
                (today_date,)
            ).fetchall()

            for row in rows:
                self.marked_today.add(row['student_id'])

            logger.info(
                f"Loaded {len(self.marked_today)} already marked "
                f"students for {today_date}"
            )
        except Exception as e:
            logger.error(f"Failed to load marked students: {e}")
        finally:
            conn.close()

    def process_recognition(self, student_id, name):
        """
        Face recognize hone par decide karega attendance
        lagani hai ya nahi.
        Returns string message for video overlay.
        """
        now = datetime.now()
        today_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")

        with self.lock:

            # ✅ Date change — reset cache and reload from DB
            if today_date != self.current_date:
                self.marked_today.clear()
                self.current_date = today_date
                self._load_todays_marked(today_date)

            # ✅ First run — load from DB
            if not self.marked_today and self.current_date == today_date:
                self._load_todays_marked(today_date)

            # ✅ Holiday check
            if is_holiday(today_date):
                logger.info(f"Holiday — no attendance for {student_id}")
                return "Holiday — No Attendance"

            # ✅ Already marked check
            if student_id in self.marked_today:
                return f"Already Marked"

            # ✅ DB insert
            success = mark_attendance(
                student_id, today_date, current_time
            )

            if success:
                self.marked_today.add(student_id)
                logger.info(
                    f"Attendance marked: {name} ({student_id}) "
                    f"at {current_time}"
                )
                return f"Marked at {current_time}"

            logger.error(
                f"Failed to mark attendance for {student_id}"
            )
            return "DB Error"

    def reset_cache(self):
        """Manual reset if needed"""
        with self.lock:
            self.marked_today.clear()
            logger.info("Attendance marker cache reset.")