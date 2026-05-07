# routes/settings_routes.py

from flask import (Blueprint, render_template, request,
                   flash, redirect, url_for, session, current_app)
from database.connection import get_db_connection
from database.queries import (
    add_holiday, get_all_holidays, delete_holiday,
    promote_all_students, get_promotion_history,
    get_last_promotion_date
)
from utils.decorators import login_required
from werkzeug.security import generate_password_hash
from datetime import datetime  # ✅ Added at top level
import logging
import re

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)

MIN_PASSWORD_LEN = 8
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$'
)


def validate_password_strength(password):
    if len(password) < MIN_PASSWORD_LEN:
        return False, f"Password must be at least {MIN_PASSWORD_LEN} characters."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number."
    return True, None


@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            if not new_password or not confirm_password:
                flash("Please fill all fields!", "warning")
                return redirect(url_for('settings.settings_page'))

            if new_password != confirm_password:
                flash("Passwords do not match!", "warning")
                return redirect(url_for('settings.settings_page'))

            valid, error_msg = validate_password_strength(new_password)
            if not valid:
                flash(error_msg, "warning")
                return redirect(url_for('settings.settings_page'))

            hashed_password = generate_password_hash(new_password)

            conn = get_db_connection()
            if conn is None:
                flash("Database connection error!", "danger")
                return redirect(url_for('settings.settings_page'))

            try:
                with conn:
                    conn.execute(
                        "UPDATE admin SET password = ?, must_change_password = 0 "
                        "WHERE username = ?",
                        (hashed_password, session.get('admin_user'))
                    )
                session['must_change_password'] = False
                flash("Password updated successfully!", "success")
                logger.info(
                    f"Password updated for admin: "
                    f"{session.get('admin_user')}"
                )

            except Exception as e:
                logger.error(f"Password update error: {e}")
                flash(f"Error updating password: {e}", "danger")

            finally:
                conn.close()

    holidays = get_all_holidays()
    promotion_history = get_promotion_history()
    last_promotion = get_last_promotion_date()

    return render_template(
        'settings.html',
        holidays=holidays,
        promotion_history=promotion_history,
        last_promotion=last_promotion
    )


@settings_bp.route('/add_holiday', methods=['POST'])
@login_required
def add_holiday_route():
    date = request.form.get('holiday_date', '').strip()
    reason = request.form.get('holiday_reason', '').strip()

    if date and reason:
        try:
            datetime.strptime(date, "%Y-%m-%d")  # ✅ Now uses top-level import
        except ValueError:
            flash("Invalid date format.", "danger")
            return redirect(url_for('settings.settings_page'))

        if len(reason) > 100:
            flash("Reason too long. Max 100 characters.", "warning")
            return redirect(url_for('settings.settings_page'))

        success = add_holiday(date, reason)
        if success:
            logger.info(f"Holiday added: {reason} on {date}")
            flash(f"Holiday added: {reason} on {date}", "success")
        else:
            logger.warning(f"Failed to add holiday: {reason} on {date}")
            flash("Holiday already exists or DB error.", "danger")
    else:
        flash("Please fill all fields.", "warning")

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/delete_holiday/<int:holiday_id>', methods=['POST'])
@login_required
def delete_holiday_route(holiday_id):
    if holiday_id <= 0:
        flash("Invalid holiday ID.", "danger")
        return redirect(url_for('settings.settings_page'))

    success = delete_holiday(holiday_id)
    if success:
        logger.info(f"Holiday {holiday_id} deleted.")
        flash("Holiday removed successfully.", "success")
    else:
        logger.warning(f"Failed to delete holiday {holiday_id}.")
        flash("Could not remove holiday.", "danger")

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/clear_attendance', methods=['POST'])
@login_required
def clear_attendance():
    confirm = request.form.get('confirm_clear', '').strip()
    if confirm != 'CLEAR':
        flash(
            "Action cancelled. You must type CLEAR to confirm.",
            "warning"
        )
        return redirect(url_for('settings.settings_page'))

    conn = get_db_connection()
    if conn is None:
        flash("Database connection error!", "danger")
        return redirect(url_for('settings.settings_page'))

    try:
        with conn:
            conn.execute("DELETE FROM attendance")
        logger.warning(
            f"All attendance cleared by {session.get('admin_user')}"
        )
        flash("All attendance records have been cleared!", "danger")

    except Exception as e:
        logger.error(f"Clear attendance error: {e}")
        flash(f"Error: {e}", "danger")

    finally:
        conn.close()

    return redirect(url_for('settings.settings_page'))


@settings_bp.route('/promote_students', methods=['POST'])
@login_required
def promote_students():
    confirm = request.form.get('confirm_promote', '').strip()
    if confirm != 'PROMOTE':
        flash(
            "Promotion cancelled. You must type PROMOTE to confirm.",
            "warning"
        )
        return redirect(url_for('settings.settings_page'))

    admin_user = session.get('admin_user', 'admin')
    result = promote_all_students(promoted_by=admin_user)

    if result['success']:
        try:
            recognizer = current_app.config.get("RECOGNIZER")
            if recognizer:
                recognizer.reload_encodings()
                logger.info("Recognizer cache reloaded after promotion.")
        except Exception as e:
            logger.warning(f"Cache reload failed after promotion: {e}")

        logger.info(
            f"Promotion by {admin_user}: "
            f"{result['promoted']} promoted, "
            f"{result['graduated']} graduated."
        )
        flash(result['message'], "success")

    else:
        logger.error(f"Promotion failed: {result['message']}")
        flash(result['message'], "danger")

    return redirect(url_for('settings.settings_page'))