# routes/auth_routes.py

from flask import (Blueprint, render_template, request,
                   redirect, url_for, session, flash)
from database.connection import get_db_connection
from werkzeug.security import check_password_hash
from functools import wraps
from urllib.parse import urlparse
import logging
import time

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

# ✅ Brute force protection — track failed attempts
# Format: {ip_address: {"count": int, "last_attempt": float}}
_failed_attempts = {}
MAX_ATTEMPTS = 5        # Max failed attempts before lockout
LOCKOUT_TIME = 300      # Lockout duration in seconds (5 minutes)


# -------------------------------
# Login Required Decorator
# -------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash("Please login first.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------
# Brute Force Helper
# -------------------------------
def is_locked_out(ip):
    """Check if IP is locked out due to too many failed attempts"""
    if ip not in _failed_attempts:
        return False

    data = _failed_attempts[ip]
    elapsed = time.time() - data['last_attempt']

    # ✅ Reset if lockout time has passed
    if elapsed > LOCKOUT_TIME:
        del _failed_attempts[ip]
        return False

    return data['count'] >= MAX_ATTEMPTS


def record_failed_attempt(ip):
    """Record a failed login attempt for IP"""
    if ip not in _failed_attempts:
        _failed_attempts[ip] = {"count": 0, "last_attempt": 0}

    _failed_attempts[ip]['count'] += 1
    _failed_attempts[ip]['last_attempt'] = time.time()

    logger.warning(
        f"Failed login attempt {_failed_attempts[ip]['count']} "
        f"from IP: {ip}"
    )


def clear_failed_attempts(ip):
    """Clear failed attempts after successful login"""
    if ip in _failed_attempts:
        del _failed_attempts[ip]


# -------------------------------
# Login Route
# -------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    # ✅ Redirect if already logged in
    if session.get('logged_in'):
        return redirect(url_for('dashboard.dashboard_page'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        ip = request.remote_addr

        # ✅ Check brute force lockout
        if is_locked_out(ip):
            remaining = int(
                LOCKOUT_TIME -
                (time.time() - _failed_attempts[ip]['last_attempt'])
            )
            flash(
                f"Too many failed attempts. "
                f"Try again in {remaining} seconds.",
                "danger"
            )
            logger.warning(f"Locked out IP attempted login: {ip}")
            return render_template('login.html')

        # ✅ Basic input validation
        if not username or not password:
            flash("Please enter username and password.", "warning")
            return render_template('login.html')

        if len(username) > 50 or len(password) > 100:
            flash("Invalid input length.", "danger")
            return render_template('login.html')

        conn = get_db_connection()
        if conn is None:
            flash("Database connection error!", "danger")
            return render_template('login.html')

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM admin WHERE username = ?",
                (username,)
            )
            admin = cursor.fetchone()

        except Exception as e:
            logger.error(f"Login DB error: {e}")
            flash("Database error. Please try again.", "danger")
            return render_template('login.html')

        finally:
            # ✅ Always close connection
            conn.close()

        # ✅ Verify password
        if admin and check_password_hash(admin['password'], password):

            # Clear failed attempts on success
            clear_failed_attempts(ip)

            session.clear()  # ✅ Clear old session data
            session['logged_in'] = True
            session['admin_user'] = admin['username']
            session['must_change_password'] = bool(
                admin['must_change_password']
            )

            logger.info(
                f"Successful login: {username} from IP: {ip}"
            )
            flash("Login Successful! Welcome Back.", "success")

            # Force secure password reset for first login/bootstrap users
            if session.get('must_change_password'):
                flash("Please change your password to continue.", "warning")
                return redirect(url_for('settings.settings_page'))

            next_page = request.args.get('next')
            # ✅ Reject external redirects: startswith('/') alone allows '//evil.com'
            if next_page:
                parsed = urlparse(next_page)
                if parsed.scheme == '' and parsed.netloc == '' and next_page.startswith('/'):
                    return redirect(next_page)
            return redirect(url_for('dashboard.dashboard_page'))

        else:
            # ✅ Record failed attempt
            record_failed_attempt(ip)
            attempts_left = MAX_ATTEMPTS - _failed_attempts[ip]['count']

            if attempts_left > 0:
                flash(
                    f"Invalid Username or Password! "
                    f"{attempts_left} attempts remaining.",
                    "danger"
                )
            else:
                flash(
                    f"Too many failed attempts. "
                    f"Account locked for {LOCKOUT_TIME // 60} minutes.",
                    "danger"
                )

    return render_template('login.html')


# -------------------------------
# Logout Route
# -------------------------------
@auth_bp.route('/logout', methods=['POST'])
def logout():
    ip = request.remote_addr
    user = session.get('admin_user', 'unknown')
    session.clear()
    logger.info(f"Admin {user} logged out from IP: {ip}")
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))