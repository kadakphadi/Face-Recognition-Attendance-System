# routes/reports_routes.py

from flask import Blueprint, render_template, request, Response
from database.queries import (
    get_attendance_by_date,
    get_student_attendance_summary,
    get_all_students
)
from utils.decorators import login_required
from datetime import datetime
import csv
import io
import re
import logging

logger = logging.getLogger(__name__)

reports_bp = Blueprint('reports', __name__)


# --------------------------------------------------
# ✅ Date Validation Helper
# --------------------------------------------------
def validate_date(date_str):
    """
    Validate date string format YYYY-MM-DD.
    Returns True if valid, False otherwise.
    """
    if not date_str:
        return False

    if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return False

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


# --------------------------------------------------
# Reports Page
# --------------------------------------------------
@reports_bp.route('/reports', methods=['GET', 'POST'])
@login_required
def reports_page():

    target_date = None
    attendance_data = []
    overall_data = []
    view_mode = 'overall'
    date_error = None

    # Get filter values
    # NOTE: For POST (date search), filters come from hidden form fields.
    if request.method == 'POST':
        selected_dept = request.form.get('department', '')
        selected_year = request.form.get('year', '')
        selected_semester = request.form.get('semester', '')
    else:
        selected_dept = request.args.get('department', '')
        selected_year = request.args.get('year', '')
        selected_semester = request.args.get('semester', '')

    selected_dept = (selected_dept or '').strip()
    selected_year = (selected_year or '').strip()
    selected_semester = (selected_semester or '').strip()

    try:
        if request.method == 'POST':
            selected = request.form.get('report_date', '').strip()

            if selected:
                if not validate_date(selected):
                    date_error = "Invalid date format. Please use YYYY-MM-DD."
                    logger.warning(
                        f"Invalid date submitted: {selected}"
                    )
                else:
                    today = datetime.now().strftime("%Y-%m-%d")
                    if selected > today:
                        date_error = "Cannot view attendance for future dates."
                        logger.warning(
                            f"Future date submitted: {selected}"
                        )
                    else:
                        target_date = selected
                        view_mode = 'date'

                        records = get_attendance_by_date(target_date)
                        for record in records:

                            if selected_dept and \
                                    record['department'] != selected_dept:
                                continue
                            if selected_year and \
                                    str(record['year']) != selected_year:
                                continue
                            if selected_semester and \
                                    str(record['semester']) != selected_semester:
                                continue

                            attendance_data.append({
                                "student_id": record['student_id'],
                                "name": record['name'],
                                "department": record['department'],
                                "year": record['year'],
                                "semester": record['semester'],
                                "time": record['time'],
                                "status": record['status']
                            })

        else:
            view_mode = 'overall'
            students = get_all_students()

            for student in students:

                if selected_dept and \
                        student['department'] != selected_dept:
                    continue
                if selected_year and \
                        str(student['year']) != selected_year:
                    continue
                if selected_semester and \
                        str(student['semester']) != selected_semester:
                    continue

                summary = get_student_attendance_summary(
                    student['student_id']
                )
                absent_days = (
                    summary['total_days'] - summary['present_days']
                ) if summary else 0

                overall_data.append({
                    "student_id": student['student_id'],
                    "name": student['name'],
                    "department": student['department'],
                    "year": student['year'],
                    "semester": student['semester'],
                    "total_days": summary['total_days'] if summary else 0,
                    "present_days": summary['present_days'] if summary else 0,
                    "absent_days": absent_days,
                    "percentage": summary['percentage'] if summary else 0.0
                })

    except Exception as e:
        logger.error(f"Reports page error: {e}")

    return render_template(
        'reports.html',
        attendance=attendance_data,
        overall=overall_data,
        selected_date=target_date,
        view_mode=view_mode,
        selected_dept=selected_dept,
        selected_year=selected_year,
        selected_semester=selected_semester,
        date_error=date_error
    )


# --------------------------------------------------
# Export CSV
# --------------------------------------------------
@reports_bp.route('/export_csv')
@login_required
def export_csv():

    target_date = request.args.get('date', '').strip()

    if not validate_date(target_date):
        logger.warning(f"Invalid date for CSV export: {target_date}")
        target_date = datetime.now().strftime("%Y-%m-%d")

    today = datetime.now().strftime("%Y-%m-%d")
    if target_date > today:
        logger.warning(
            f"Future date CSV export attempted: {target_date}"
        )
        target_date = today

    selected_dept = request.args.get('department', '')
    selected_year = request.args.get('year', '')
    selected_semester = request.args.get('semester', '')

    attendance_data = get_attendance_by_date(target_date)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student ID", "Name", "Department",
        "Year", "Semester", "Time", "Status"
    ])

    for row in attendance_data:

        if selected_dept and row['department'] != selected_dept:
            continue
        if selected_year and str(row['year']) != selected_year:
            continue
        if selected_semester and \
                str(row['semester']) != selected_semester:
            continue

        writer.writerow([
            row["student_id"],
            row["name"],
            row["department"],
            row["year"],
            row["semester"],
            row["time"],
            row["status"]
        ])

    safe_date = re.sub(r'[^0-9\-]', '', target_date)

    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            f"attachment; filename=attendance_{safe_date}.csv"
        }
    )

    return response