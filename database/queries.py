# database/queries.py

import sqlite3
import logging
import numpy as np
from database.connection import get_db_connection
from datetime import datetime

logger = logging.getLogger(__name__)


# -------------------------------
# ADD STUDENT
# -------------------------------
def add_student(student_id, name, father_name,
                department, mobile, year, semester, encoding):
    """Naya student database mein save karne ke liye"""

    sql = '''INSERT INTO students 
             (student_id, name, father_name, department,
              mobile_number, year, semester, face_encoding)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?)'''

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        # ✅ Use numpy instead of pickle for safe serialization
        encoding_blob = encoding.tobytes()

        with conn:
            conn.execute(sql, (
                student_id,
                name,
                father_name,
                department,
                mobile,
                year,
                semester,
                encoding_blob
            ))
        return True

    except sqlite3.IntegrityError:
        logger.error(f"Student ID {student_id} already exists.")
        return False
    except sqlite3.Error as e:
        logger.error(f"Student add failed: {e}")
        return False
    finally:
        conn.close()


# -------------------------------
# GET ALL STUDENTS
# -------------------------------
def get_all_students():
    """Saare students fetch karne ke liye"""
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_id, name, father_name,
                   department, year, semester, mobile_number
            FROM students
            WHERE COALESCE(is_active, 1) = 1
            ORDER BY id DESC
        """)
        return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Fetch students failed: {e}")
        return []
    finally:
        conn.close()


# -------------------------------
# MARK ATTENDANCE
# -------------------------------
def mark_attendance(student_id, date, time, status="Present"):
    """Attendance mark karna (duplicate automatically ignore hoga)"""

    sql = '''INSERT OR IGNORE INTO attendance 
             (student_id, date, time, status) 
             VALUES (?, ?, ?, ?)'''

    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn:
            result = conn.execute(sql, (student_id, date, time, status))
            if result.rowcount == 0:
                logger.info(
                    f"Attendance already marked for {student_id} today."
                )
                return False
        return True

    except sqlite3.Error as e:
        logger.error(f"Attendance mark failed: {e}")
        return False
    finally:
        conn.close()


# -------------------------------
# DELETE STUDENT
# -------------------------------
def delete_student(student_id):
    """
    Soft-delete student — attendance history preserved.
    We keep the row for FK/history joins, but disable face encoding.
    """
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        with conn:
            # Keep record for history joins; disable from active lists.
            # face_encoding is NOT NULL in schema, so store empty blob.
            conn.execute("""
                UPDATE students
                SET is_active = 0,
                    face_encoding = ?
                WHERE student_id = ?
            """, (sqlite3.Binary(b''), student_id))
        logger.info(
            f"Student {student_id} deactivated (soft delete). "
            f"Attendance kept."
        )
        return True

    except sqlite3.Error as e:
        logger.error(f"Delete student failed: {e}")
        return False
    finally:
        conn.close()


# -------------------------------
# HOLIDAYS MANAGEMENT
# -------------------------------
def add_holiday(date, reason):
    """Add a holiday to the database"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn:
            conn.execute(
                "INSERT INTO holidays (date, reason) VALUES (?, ?)",
                (date, reason)
            )
        return True
    except Exception as e:
        logger.error(f"Add holiday error: {e}")
        return False
    finally:
        conn.close()  # ✅ Fixed — was missing


def get_all_holidays():
    """Get all holidays"""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        return conn.execute(
            "SELECT * FROM holidays ORDER BY date ASC"
        ).fetchall()
    except Exception as e:
        logger.error(f"Get holidays error: {e}")
        return []
    finally:
        conn.close()  # ✅ Fixed — was missing


def delete_holiday(holiday_id):
    """Delete a holiday"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        with conn:
            conn.execute(
                "DELETE FROM holidays WHERE id = ?",
                (holiday_id,)
            )
        return True
    except Exception as e:
        logger.error(f"Delete holiday error: {e}")
        return False
    finally:
        conn.close()  # ✅ Fixed — was missing


def is_holiday(date):
    """Check if a specific date is a holiday"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        result = conn.execute(
            "SELECT id FROM holidays WHERE date = ?",
            (date,)
        ).fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Holiday check error: {e}")
        return False
    finally:
        conn.close()  # ✅ Fixed — was missing


def get_working_days_count():
    """Get total working days excluding holidays"""
    conn = get_db_connection()
    if not conn:
        return 0
    try:
        result = conn.execute("""
            SELECT COUNT(DISTINCT date) FROM attendance
            WHERE date NOT IN (
                SELECT date FROM holidays
            )
        """).fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Working days count error: {e}")
        return 0
    finally:
        conn.close()  # ✅ Fixed — was missing


# -------------------------------
# ATTENDANCE REPORT BY DATE
# -------------------------------
def get_attendance_by_date(target_date):
    """Specific date ki attendance report"""

    sql = '''
        SELECT students.student_id,
               students.name,
               students.department,
               students.year,
               students.semester,
               attendance.time,
               attendance.status
        FROM students
        JOIN attendance ON students.student_id = attendance.student_id
        WHERE attendance.date = ?
        ORDER BY attendance.time
    '''

    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (target_date,))
        return cursor.fetchall()

    except sqlite3.Error as e:
        logger.error(f"Report fetch failed: {e}")
        return []
    finally:
        conn.close()


# -------------------------------
# STUDENT ATTENDANCE SUMMARY
# -------------------------------
def get_student_attendance_summary(student_id):
    """Get total days, present days and percentage for a student"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()

        # ✅ Fixed — count only days when at least one
        # student was present (global working days)
        total_days = cursor.execute("""
            SELECT COUNT(DISTINCT date) FROM attendance
            WHERE date NOT IN (
                SELECT date FROM holidays
            )
        """).fetchone()[0]

        present_days = cursor.execute("""
            SELECT COUNT(*) FROM attendance
            WHERE student_id = ?
            AND date NOT IN (
                SELECT date FROM holidays
            )
        """, (student_id,)).fetchone()[0]

        if total_days == 0:
            return {
                "total_days": 0,
                "present_days": 0,
                "percentage": 0.0
            }

        percentage = round((present_days / total_days) * 100, 2)

        return {
            "total_days": total_days,
            "present_days": present_days,
            "percentage": percentage
        }

    except Exception as e:
        logger.error(f"Attendance summary error: {e}")
        return None
    finally:
        conn.close()


# -----------------------------------------------
# SEMESTER PROMOTION
# -----------------------------------------------
def promote_all_students(promoted_by="admin"):
    """
    Promote all students to next semester.
    Semester 6 students moved to alumni table.
    Entire operation wrapped in single transaction.
    """
    conn = get_db_connection()
    if not conn:
        return {
            "success": False,
            "message": "Database connection failed.",
            "promoted": 0,
            "graduated": 0
        }

    try:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        passing_year = datetime.now().year

        students = cursor.execute(
            "SELECT student_id, name, father_name, "
            "department, mobile_number, year, semester "
            "FROM students"
        ).fetchall()

        promoted_count = 0
        graduated_count = 0
        graduated_ids = []

        # ✅ Single transaction for entire promotion
        cursor.execute("BEGIN TRANSACTION")

        for student in students:
            current_sem = student['semester']
            student_id = student['student_id']

            if current_sem >= 6:
                cursor.execute("""
                    INSERT OR IGNORE INTO alumni
                    (student_id, name, father_name, department,
                     mobile_number, year, passing_semester,
                     passing_year, graduated_on)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    student_id,
                    student['name'],
                    student['father_name'],
                    student['department'],
                    student['mobile_number'],
                    student['year'],
                    current_sem,
                    passing_year,
                    today
                ))

                # ✅ Only count if actually inserted
                if cursor.rowcount > 0:
                    graduated_ids.append(student_id)
                    graduated_count += 1
                    logger.info(
                        f"Student {student_id} graduated "
                        f"and moved to alumni."
                    )
                else:
                    logger.warning(
                        f"Student {student_id} already in alumni. Skipped."
                    )

            else:
                next_sem = current_sem + 1
                next_year = (next_sem + 1) // 2

                cursor.execute("""
                    UPDATE students
                    SET semester = ?, year = ?
                    WHERE student_id = ?
                """, (next_sem, next_year, student_id))

                promoted_count += 1
                logger.info(
                    f"Student {student_id} promoted: "
                    f"Sem {current_sem} → Sem {next_sem}"
                )

        # Delete graduated students from active table (Soft delete to keep attendance history)
        for student_id in graduated_ids:
            cursor.execute("""
                UPDATE students
                SET is_active = 0,
                    face_encoding = ?
                WHERE student_id = ?
            """, (sqlite3.Binary(b''), student_id))
            logger.info(
                f"Student {student_id} deactivated (soft delete). Attendance kept."
            )

        # Log promotion event
        cursor.execute("""
            INSERT INTO promotion_log
            (promoted_on, total_promoted, total_graduated, promoted_by)
            VALUES (?, ?, ?, ?)
        """, (today, promoted_count, graduated_count, promoted_by))

        # ✅ Commit entire transaction at once
        conn.commit()

        logger.info(
            f"Promotion complete: {promoted_count} promoted, "
            f"{graduated_count} graduated by {promoted_by}"
        )

        return {
            "success": True,
            "message": (
                f"{promoted_count} students promoted to next semester. "
                f"{graduated_count} students graduated and moved to alumni."
            ),
            "promoted": promoted_count,
            "graduated": graduated_count
        }

    except Exception as e:
        # ✅ Rollback entire promotion if anything fails
        conn.rollback()
        logger.error(f"Promotion failed — rolled back: {e}")
        return {
            "success": False,
            "message": f"Promotion failed and was rolled back: {e}",
            "promoted": 0,
            "graduated": 0
        }
    finally:
        conn.close()


# -----------------------------------------------
# GET PROMOTION HISTORY
# -----------------------------------------------
def get_promotion_history():
    """Get all past promotion events"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        return conn.execute("""
            SELECT * FROM promotion_log
            ORDER BY created_at DESC
        """).fetchall()
    except Exception as e:
        logger.error(f"Promotion history error: {e}")
        return []
    finally:
        conn.close()


# -----------------------------------------------
# GET ALL ALUMNI
# -----------------------------------------------
def get_all_alumni(department=None, passing_year=None):
    """Get all graduated students with optional filters"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        query = "SELECT * FROM alumni WHERE 1=1"
        params = []

        if department:
            query += " AND department = ?"
            params.append(department)

        if passing_year:
            query += " AND passing_year = ?"
            params.append(passing_year)

        query += " ORDER BY graduated_on DESC"

        return conn.execute(query, params).fetchall()

    except Exception as e:
        logger.error(f"Get alumni error: {e}")
        return []
    finally:
        conn.close()


# -----------------------------------------------
# GET ALUMNI PASSING YEARS
# -----------------------------------------------
def get_alumni_passing_years():
    """Get all distinct passing years for filter"""
    conn = get_db_connection()
    if not conn:
        return []

    try:
        return conn.execute("""
            SELECT DISTINCT passing_year
            FROM alumni
            ORDER BY passing_year DESC
        """).fetchall()
    except Exception as e:
        logger.error(f"Get passing years error: {e}")
        return []
    finally:
        conn.close()


# -----------------------------------------------
# GET LAST PROMOTION DATE
# -----------------------------------------------
def get_last_promotion_date():
    """Get date of most recent promotion"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        result = conn.execute("""
            SELECT promoted_on FROM promotion_log
            ORDER BY created_at DESC
            LIMIT 1
        """).fetchone()
        return result['promoted_on'] if result else None
    except Exception as e:
        logger.error(f"Get last promotion date error: {e}")
        return None
    finally:
        conn.close()