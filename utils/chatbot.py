# utils/chatbot.py
import re
import logging
from database.connection import get_db_connection
from datetime import datetime

logger = logging.getLogger(__name__)


class AttendanceChatbot:

    def __init__(self):
        self.MIN_ATTENDANCE = 75

    def get_response(self, message):
        message = message.strip().lower()

        try:
            if any(word in message for word in
                   ['hello', 'hi', 'hey', 'help']):
                return self._greeting()

            elif any(word in message for word in
                     ['attendance', 'present', 'absent',
                      'percentage', '%']):
                student_id = self._extract_student_id(message)
                if student_id:
                    return self._get_attendance_summary(student_id)
                return self._ask_for_student_id()

            elif any(word in message for word in
                     ['history', 'record', 'log']):
                student_id = self._extract_student_id(message)
                if student_id:
                    return self._get_attendance_history(student_id)
                return self._ask_for_student_id()

            elif any(word in message for word in
                     ['shortage', 'low', 'warning', 'danger', 'risk']):
                return self._get_shortage_list()

            elif any(word in message for word in
                     ['total', 'count', 'how many', 'students']):
                return self._get_total_students()

            elif any(word in message for word in
                     ['today', 'present today']):
                return self._get_today_attendance()

            elif any(word in message for word in
                     ['department', 'dept', 'branch']):
                return self._get_department_stats()

            else:
                return self._default_response()

        except Exception as e:
            logger.error(f"Chatbot error: {e}")
            return {
                "message": "Sorry, kuch problem aa gayi. Please try again.",
                "type": "error"
            }

    def _extract_student_id(self, message):
        match = re.search(r'\b\d{4,6}\b', message)
        return match.group() if match else None

    def _greeting(self):
        return {
            "message": (
                "👋 Hello! I am your Smart Attendance Assistant.\n\n"
                "I can help you with:\n"
                "• Check attendance % → type 'attendance 21001'\n"
                "• View history → type 'history 21001'\n"
                "• Shortage warning → type 'shortage list'\n"
                "• Today's attendance → type 'today'\n"
                "• Department stats → type 'department stats'\n"
                "• Total students → type 'total students'"
            ),
            "type": "info"
        }

    def _ask_for_student_id(self):
        return {
            "message": (
                "Please provide a Student ID with your query.\n"
                "Example: 'attendance 21001'"
            ),
            "type": "warning"
        }

    def _get_attendance_summary(self, student_id):
        conn = get_db_connection()
        if not conn:
            return {"message": "Database connection error.", "type": "error"}

        try:
            cursor = conn.cursor()

            student = cursor.execute(
                "SELECT name, department FROM students "
                "WHERE student_id = ?",
                (student_id,)
            ).fetchone()

            if not student:
                return {
                    "message": f"❌ Student ID {student_id} not found.",
                    "type": "error"
                }

            total_days = cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM attendance
                WHERE date NOT IN (SELECT date FROM holidays)
            """).fetchone()[0]

            present_days = cursor.execute("""
                SELECT COUNT(*) FROM attendance
                WHERE student_id = ?
                AND date NOT IN (SELECT date FROM holidays)
            """, (student_id,)).fetchone()[0]

            if total_days == 0:
                return {
                    "message": (
                        f"No attendance records found yet "
                        f"for {student['name']}."
                    ),
                    "type": "info"
                }

            percentage = round((present_days / total_days) * 100, 2)
            absent_days = total_days - present_days

            if percentage < 75:
                needed = 0
                temp_present = present_days
                temp_total = total_days
                # ✅ Max 1000 iterations to prevent infinite loop
                while needed < 1000:
                    if round((temp_present / temp_total) * 100, 2) >= 75:
                        break
                    temp_present += 1
                    temp_total += 1
                    needed += 1
                suggestion = (
                    f"⚠️ Need to attend {needed} more classes "
                    f"to reach 75%."
                )
            else:
                can_miss = 0
                temp_present = present_days
                temp_total = total_days
                # ✅ Max 1000 iterations to prevent infinite loop
                while can_miss < 1000:
                    temp_total += 1
                    new_pct = round(
                        (temp_present / temp_total) * 100, 2
                    )
                    if new_pct < 75:
                        break
                    can_miss += 1
                suggestion = (
                    f"✅ Can afford to miss {can_miss} more classes."
                )

            if percentage >= 90:
                status = "🟢 Excellent"
            elif percentage >= 75:
                status = "🟡 Safe"
            elif percentage >= 60:
                status = "🟠 Warning"
            else:
                status = "🔴 Critical - Shortage!"

            return {
                "message": (
                    f"📊 Attendance Report\n"
                    f"──────────────────\n"
                    f"Student : {student['name']}\n"
                    f"Dept    : {student['department']}\n"
                    f"Present : {present_days} days\n"
                    f"Absent  : {absent_days} days\n"
                    f"Total   : {total_days} working days\n"
                    f"Percent : {percentage}%\n"
                    f"Status  : {status}\n"
                    f"──────────────────\n"
                    f"{suggestion}"
                ),
                "type": "success" if percentage >= 75 else "warning"
            }

        except Exception as e:
            logger.error(
                f"Attendance summary error for {student_id}: {e}"
            )
            return {
                "message": "Error fetching attendance summary.",
                "type": "error"
            }
        finally:
            conn.close()

    def _get_attendance_history(self, student_id):
        conn = get_db_connection()
        if not conn:
            return {"message": "Database connection error.", "type": "error"}

        try:
            cursor = conn.cursor()

            student = cursor.execute(
                "SELECT name FROM students WHERE student_id = ?",
                (student_id,)
            ).fetchone()

            if not student:
                return {
                    "message": f"❌ Student ID {student_id} not found.",
                    "type": "error"
                }

            records = cursor.execute("""
                SELECT date, time FROM attendance
                WHERE student_id = ?
                ORDER BY date DESC LIMIT 7
            """, (student_id,)).fetchall()

            if not records:
                return {
                    "message": (
                        f"No attendance history found "
                        f"for {student['name']}."
                    ),
                    "type": "info"
                }

            history = "\n".join([
                f"📅 {r['date']} at {r['time']}"
                for r in records
            ])

            return {
                "message": (
                    f"📋 Last {len(records)} records "
                    f"for {student['name']}:\n\n{history}"
                ),
                "type": "success"
            }

        except Exception as e:
            logger.error(
                f"Attendance history error for {student_id}: {e}"
            )
            return {
                "message": "Error fetching history.",
                "type": "error"
            }
        finally:
            conn.close()

    def _get_shortage_list(self):
        conn = get_db_connection()
        if not conn:
            return {"message": "Database connection error.", "type": "error"}

        try:
            cursor = conn.cursor()

            total_days = cursor.execute("""
                SELECT COUNT(DISTINCT date) FROM attendance
                WHERE date NOT IN (SELECT date FROM holidays)
            """).fetchone()[0]

            if total_days == 0:
                return {
                    "message": "No attendance data available yet.",
                    "type": "info"
                }

            # ✅ Single optimized query instead of N queries in loop
            shortage_rows = cursor.execute("""
                SELECT
                    s.student_id,
                    s.name,
                    s.department,
                    COUNT(a.id) as present_count
                FROM students s
                LEFT JOIN attendance a
                    ON s.student_id = a.student_id
                    AND a.date NOT IN (SELECT date FROM holidays)
                GROUP BY s.student_id, s.name, s.department
                HAVING ROUND(COUNT(a.id) * 100.0 / ?, 2) < ?
                ORDER BY present_count ASC
            """, (total_days, self.MIN_ATTENDANCE)).fetchall()

            if not shortage_rows:
                return {
                    "message": (
                        "✅ Great! No students have attendance shortage."
                    ),
                    "type": "success"
                }

            shortage_list = []
            for row in shortage_rows:
                pct = round(
                    (row['present_count'] / total_days) * 100, 2
                )
                shortage_list.append(
                    f"⚠️ {row['name']} ({row['student_id']}) - {pct}%"
                )

            return {
                "message": (
                    "🔴 Students below 75%:\n\n" +
                    "\n".join(shortage_list)
                ),
                "type": "warning"
            }

        except Exception as e:
            logger.error(f"Shortage list error: {e}")
            return {
                "message": "Error fetching shortage list.",
                "type": "error"
            }
        finally:
            conn.close()

    def _get_total_students(self):
        conn = get_db_connection()
        if not conn:
            return {"message": "Database connection error.", "type": "error"}

        try:
            cursor = conn.cursor()
            total = cursor.execute(
                "SELECT COUNT(*) FROM students "
                "WHERE COALESCE(is_active, 1) = 1"
            ).fetchone()[0]
            return {
                "message": (
                    f"👥 Total registered students in system: {total}"
                ),
                "type": "info"
            }

        except Exception as e:
            logger.error(f"Total students error: {e}")
            return {
                "message": "Error fetching student count.",
                "type": "error"
            }
        finally:
            conn.close()

    def _get_today_attendance(self):
        conn = get_db_connection()
        if not conn:
            return {"message": "Database connection error.", "type": "error"}

        try:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")

            present = cursor.execute(
                "SELECT COUNT(*) FROM attendance WHERE date = ?",
                (today,)
            ).fetchone()[0]

            total = cursor.execute(
                "SELECT COUNT(*) FROM students"
            ).fetchone()[0]

            percentage = round(
                (present / total) * 100, 2
            ) if total > 0 else 0

            # ✅ Renamed variable to avoid conflict with
            # is_holiday function name
            holiday_row = cursor.execute(
                "SELECT reason FROM holidays WHERE date = ?",
                (today,)
            ).fetchone()

            if holiday_row:
                return {
                    "message": (
                        f"📅 Today ({today}) is a Holiday!\n"
                        f"Reason: {holiday_row['reason']}\n"
                        f"No attendance today."
                    ),
                    "type": "warning"
                }

            return {
                "message": (
                    f"📅 Today's Attendance ({today})\n"
                    f"Present: {present} / {total} students\n"
                    f"Percentage: {percentage}%"
                ),
                "type": "info"
            }

        except Exception as e:
            logger.error(f"Today attendance error: {e}")
            return {
                "message": "Error fetching today's attendance.",
                "type": "error"
            }
        finally:
            conn.close()

    def _get_department_stats(self):
        conn = get_db_connection()
        if not conn:
            return {"message": "Database connection error.", "type": "error"}

        try:
            cursor = conn.cursor()

            # ✅ Single query instead of N queries in loop
            dept_rows = cursor.execute("""
                SELECT department, COUNT(*) as total
                FROM students
                GROUP BY department
                ORDER BY department
            """).fetchall()

            if not dept_rows:
                return {
                    "message": "No department data found.",
                    "type": "info"
                }

            stats = [
                f"🏫 {row['department']}: {row['total']} students"
                for row in dept_rows
            ]

            return {
                "message": (
                    "📊 Department wise students:\n\n" +
                    "\n".join(stats)
                ),
                "type": "info"
            }

        except Exception as e:
            logger.error(f"Department stats error: {e}")
            return {
                "message": "Error fetching department stats.",
                "type": "error"
            }
        finally:
            conn.close()

    def _default_response(self):
        return {
            "message": (
                "🤔 I didn't understand that.\n\n"
                "Try these commands:\n"
                "• 'attendance 21001'\n"
                "• 'history 21001'\n"
                "• 'shortage list'\n"
                "• 'today'\n"
                "• 'department stats'\n"
                "• 'total students'\n"
                "• 'help'"
            ),
            "type": "info"
        }