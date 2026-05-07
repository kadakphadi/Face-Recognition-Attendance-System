# routes/dashboard_routes.py

from flask import Blueprint, render_template, jsonify
from database.connection import get_db_connection
from utils.decorators import login_required
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard_page():
    """Main Dashboard with branch + semester wise attendance"""

    today = datetime.now().strftime("%Y-%m-%d")

    stats = {
        "total_students": 0,
        "present_today": 0,
        "branch_stats": []
    }

    conn = get_db_connection()
    if conn is None:
        return render_template(
            'dashboard.html',
            stats=stats,
            today=today  # ✅ Always pass today
        )

    try:
        cursor = conn.cursor()

        # Total Students
        stats["total_students"] = cursor.execute(
            "SELECT COUNT(*) FROM students WHERE COALESCE(is_active, 1) = 1"
        ).fetchone()[0]

        # Today's total attendance
        stats["present_today"] = cursor.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?",
            (today,)
        ).fetchone()[0]

        # ✅ Get all unique departments
        departments = cursor.execute(
            "SELECT DISTINCT department FROM students "
            "WHERE COALESCE(is_active, 1) = 1 "
            "ORDER BY department"
        ).fetchall()

        branch_stats = []

        for dept_row in departments:
            dept = dept_row['department']

            # Get all unique semesters for this department
            semesters = cursor.execute("""
                SELECT DISTINCT semester
                FROM students
                WHERE department = ?
                  AND COALESCE(is_active, 1) = 1
                ORDER BY semester
            """, (dept,)).fetchall()

            semester_data = []

            for sem_row in semesters:
                sem = sem_row['semester']

                # Total students in this dept + semester
                total = cursor.execute("""
                    SELECT COUNT(*) FROM students
                    WHERE department = ? AND semester = ?
                      AND COALESCE(is_active, 1) = 1
                """, (dept, sem)).fetchone()[0]

                # Present today in this dept + semester
                present = cursor.execute("""
                    SELECT COUNT(*) FROM attendance
                    JOIN students
                    ON students.student_id = attendance.student_id
                    WHERE attendance.date = ?
                    AND students.department = ?
                    AND students.semester = ?
                """, (today, dept, sem)).fetchone()[0]

                absent = total - present
                percentage = round(
                    (present / total * 100), 1
                ) if total > 0 else 0

                semester_data.append({
                    "semester": sem,
                    "total": total,
                    "present": present,
                    "absent": absent,
                    "percentage": percentage
                })

            # Total for entire department
            dept_total = cursor.execute("""
                SELECT COUNT(*) FROM students
                WHERE department = ?
                  AND COALESCE(is_active, 1) = 1
            """, (dept,)).fetchone()[0]

            dept_present = cursor.execute("""
                SELECT COUNT(*) FROM attendance
                JOIN students
                ON students.student_id = attendance.student_id
                WHERE attendance.date = ?
                AND students.department = ?
            """, (today, dept)).fetchone()[0]

            dept_percentage = round(
                (dept_present / dept_total * 100), 1
            ) if dept_total > 0 else 0

            branch_stats.append({
                "department": dept,
                "total": dept_total,
                "present": dept_present,
                "absent": dept_total - dept_present,
                "percentage": dept_percentage,
                "semesters": semester_data
            })

        stats["branch_stats"] = branch_stats

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
    finally:
        conn.close()

    # ✅ Pass both stats and today to template
    return render_template(
        'dashboard.html',
        stats=stats,
        today=today
    )


# --------------------------------------------------
# API: Today's Attendance Count
# --------------------------------------------------
@dashboard_bp.route('/api/today_count')
@login_required
def today_count():
    """Return today's attendance count as JSON"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"count": 0})

    try:
        today = datetime.now().strftime("%Y-%m-%d")
        count = conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?",
            (today,)
        ).fetchone()[0]
        return jsonify({"count": count})

    except Exception as e:
        logger.error(f"Today count API error: {e}")
        return jsonify({"count": 0})
    finally:
        conn.close()


# --------------------------------------------------
# API: Recent Attendance Logs
# --------------------------------------------------
@dashboard_bp.route('/api/recent_attendance')
@login_required
def recent_attendance():
    """Return last 10 attendance records as JSON"""
    conn = get_db_connection()
    if conn is None:
        return jsonify({"records": []})

    try:
        today = datetime.now().strftime("%Y-%m-%d")

        rows = conn.execute("""
            SELECT students.name,
                   students.department,
                   attendance.time,
                   attendance.student_id
            FROM attendance
            JOIN students
            ON students.student_id = attendance.student_id
            WHERE attendance.date = ?
            ORDER BY attendance.time DESC
            LIMIT 10
        """, (today,)).fetchall()

        records = []
        for row in rows:
            records.append({
                "name": row["name"],
                "department": row["department"],
                "time": row["time"],
                "student_id": row["student_id"]
            })

        return jsonify({"records": records})

    except Exception as e:
        logger.error(f"Recent attendance API error: {e}")
        return jsonify({"records": []})
    finally:
        conn.close()