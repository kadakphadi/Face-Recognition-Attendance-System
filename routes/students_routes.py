# routes/students_routes.py

from flask import Blueprint, render_template, flash, redirect, url_for, request
from database.connection import get_db_connection
from database.queries import delete_student
from utils.decorators import login_required
import re
import logging

logger = logging.getLogger(__name__)

students_bp = Blueprint('students', __name__)


# --------------------------------------------------
# ✅ Get Students with SQL Filters
# Much faster than Python filtering for 350+ students
# --------------------------------------------------
def get_students_filtered(department=None, year=None, semester=None):
    """Fetch students from DB with optional SQL filters"""

    conn = get_db_connection()
    if conn is None:
        return []

    try:
        # ✅ Build query dynamically with SQL filters
        query = """
            SELECT student_id, name, father_name,
                   department, year, semester, mobile_number
            FROM students
            WHERE COALESCE(is_active, 1) = 1
        """
        params = []

        if department:
            query += " AND department = ?"
            params.append(department)

        if year:
            try:
                query += " AND year = ?"
                params.append(int(year))
            except ValueError:
                logger.warning(f"Invalid year filter: {year}")

        if semester:
            try:
                query += " AND semester = ?"
                params.append(int(semester))
            except ValueError:
                logger.warning(f"Invalid semester filter: {semester}")

        query += " ORDER BY id DESC"

        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    except Exception as e:
        logger.error(f"Fetch students failed: {e}")
        return []
    finally:
        conn.close()


# --------------------------------------------------
# Students Page
# --------------------------------------------------
@students_bp.route('/students')
@login_required
def students_page():
    """Saare registered students ki list dikhane ke liye"""

    # Get filter values from query params
    selected_dept = request.args.get('department', '').strip()
    selected_year = request.args.get('year', '').strip()
    selected_semester = request.args.get('semester', '').strip()

    # ✅ Validate year and semester values
    if selected_year and selected_year not in ['1', '2', '3']:
        logger.warning(f"Invalid year filter: {selected_year}")
        selected_year = ''

    if selected_semester and selected_semester not in \
            ['1', '2', '3', '4', '5', '6']:
        logger.warning(f"Invalid semester filter: {selected_semester}")
        selected_semester = ''

    # ✅ Fetch with SQL filters — much faster than Python filtering
    students = get_students_filtered(
        department=selected_dept if selected_dept else None,
        year=selected_year if selected_year else None,
        semester=selected_semester if selected_semester else None
    )

    logger.info(
        f"Students page loaded: {len(students)} records "
        f"(dept={selected_dept}, year={selected_year}, "
        f"sem={selected_semester})"
    )

    return render_template(
        'students.html',
        students=students,
        selected_dept=selected_dept,
        selected_year=selected_year,
        selected_semester=selected_semester
    )


# --------------------------------------------------
# Delete Student
# --------------------------------------------------
@students_bp.route('/delete_student/<string:student_id>', methods=['POST'])
@login_required
def remove_student(student_id):
    """Specific student ko delete karne ka route"""

    # ✅ Validate student_id format
    if not student_id or len(student_id) > 20:
        flash("Invalid student ID!", "warning")
        return redirect(url_for('students.students_page'))

    # ✅ Only allow alphanumeric, dash, underscore
    if not re.match(r'^[a-zA-Z0-9_-]+$', student_id):
        flash("Invalid student ID format!", "warning")
        logger.warning(
            f"Invalid student ID format in delete: {student_id}"
        )
        return redirect(url_for('students.students_page'))

    success = delete_student(student_id)

    if success:
        logger.info(f"Student {student_id} deleted successfully.")
        flash(
            f"Student {student_id} deleted successfully.",
            "success"
        )
    else:
        logger.error(f"Failed to delete student {student_id}.")
        flash("Could not delete student. Try again.", "danger")

    return redirect(url_for('students.students_page'))