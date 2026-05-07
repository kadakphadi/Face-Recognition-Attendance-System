# routes/alumni_routes.py

from flask import Blueprint, render_template, request
from database.queries import get_all_alumni, get_alumni_passing_years
from utils.decorators import login_required
import logging

logger = logging.getLogger(__name__)

alumni_bp = Blueprint('alumni', __name__)


@alumni_bp.route('/alumni')
@login_required
def alumni_page():
    """Show all graduated students with filters"""

    # ✅ Get filter values
    selected_dept = request.args.get('department', '')
    selected_year = request.args.get('passing_year', '')

    try:
        # ✅ Fetch alumni with filters
        alumni_list = get_all_alumni(
            department=selected_dept if selected_dept else None,
            passing_year=int(selected_year) if selected_year and selected_year.isdigit() else None
        )

        # ✅ Get all passing years for dropdown
        passing_years = get_alumni_passing_years()

        logger.info(
            f"Alumni page loaded: {len(alumni_list)} records "
            f"(dept={selected_dept}, year={selected_year})"
        )

    except Exception as e:
        logger.error(f"Alumni page error: {e}")
        alumni_list = []
        passing_years = []

    return render_template(
        'alumni.html',
        alumni=alumni_list,
        passing_years=passing_years,
        selected_dept=selected_dept,
        selected_year=selected_year
    )