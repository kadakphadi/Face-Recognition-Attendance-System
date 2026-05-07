# utils/decorators.py
from functools import wraps
from flask import session, redirect, url_for, flash, request
import logging

logger = logging.getLogger(__name__)

LOGIN_SESSION_KEY = "logged_in"

def login_required(f):
    """
    Custom decorator:
    Checks whether admin/user is logged in.
    If not, redirects to login page and remembers requested URL.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not session.get(LOGIN_SESSION_KEY):
            flash("Please login to access this page!", "warning")

            # ✅ Use request.path (relative) instead of
            # request.url (absolute) to prevent open redirect
            next_url = request.path
            logger.warning(f"Unauthenticated access attempt to: {next_url}")

            return redirect(url_for('auth.login', next=next_url))

        # If password reset is required, allow only settings/logout paths.
        if session.get("must_change_password"):
            endpoint = request.endpoint or ""
            allowed = {
                "settings.settings_page",
                "auth.logout",
                "static"
            }
            if endpoint not in allowed:
                flash("Please change password before continuing.", "warning")
                return redirect(url_for("settings.settings_page"))

        return f(*args, **kwargs)

    return decorated_function