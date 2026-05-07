# app.py

from flask import Flask, session, redirect, url_for
from config import Config, init_directories
from database.connection import get_db_connection
from database.schema import create_tables
from utils.logger import log_info, log_error
from werkzeug.security import generate_password_hash
import os
import secrets


# ---------------------------
# App Factory
# ---------------------------
def create_app():
    """Create Flask app using factory pattern"""

    # ✅ Create required directories first
    init_directories()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # ✅ SECRET_KEY already set by Config — no need to set again
    # app.config.from_object(Config) handles it correctly

    # ---------------------------
    # Register Blueprints
    # ---------------------------
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.registration_routes import registration_bp
    from routes.attendance_routes import attendance_bp
    from routes.students_routes import students_bp
    from routes.reports_routes import reports_bp
    from routes.settings_routes import settings_bp
    from routes.chatbot_routes import chatbot_bp
    from routes.alumni_routes import alumni_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(alumni_bp)

    # ---------------------------
    # Root route
    # ---------------------------
    @app.route('/')
    def index():
        if session.get('logged_in'):
            return redirect(url_for('dashboard.dashboard_page'))
        return redirect(url_for('auth.login'))

    # ---------------------------
    # Initialize system + cache
    # ---------------------------
    with app.app_context():
        init_system()

        # Pre-load recognizer cache at startup
        try:
            from modules.recognizer import FaceRecognizer
            recognizer = FaceRecognizer()
            recognizer.load_encodings()
            app.config["RECOGNIZER"] = recognizer
            log_info(
                f"Recognizer ready: "
                f"{len(recognizer.known_encodings)} students cached."
            )
        except Exception as e:
            log_error(f"Recognizer initialization failed: {e}")
            app.config["RECOGNIZER"] = None

        # Camera initialized lazily on demand
        app.config["CAMERA"] = None

    return app


# ---------------------------
# System Initialization
# ---------------------------
def init_system():
    """Initialize database tables and default admin"""
    try:
        create_tables()

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM ADMIN WHERE username = ?", ('ADMIN',)
                )
                admin = cursor.fetchone()

                if not admin:
                    initial_password = os.environ.get("ADMIN_INITIAL_PASSWORD")
                    must_change_password = 1

                    if not initial_password:
                        # Generate non-predictable bootstrap password
                        initial_password = secrets.token_urlsafe(12)
                        log_error(
                            "SECURITY WARNING: ADMIN_INITIAL_PASSWORD not set. "
                            "Generated one-time bootstrap admin password. "
                            f"Username: admin / Password: {initial_password}"
                        )

                    hashed_pass = generate_password_hash(initial_password)
                    cursor.execute(
                        "INSERT INTO admin (username, password, must_change_password) "
                        "VALUES (?, ?, ?)",
                        ('admin', hashed_pass, must_change_password)
                    )
                    conn.commit()
                    log_info(
                        "Initial admin created successfully. "
                        "Password change is mandatory on first login."
                    )

            finally:
                conn.close()

        log_info("System initialized successfully.")

    except Exception as e:
        log_error(f"Initialization Error: {e}")


if __name__ == '__main__':
    # ---------------------------
    # Run Server
    # ---------------------------
    app = create_app()
    log_info("Starting Flask Server on http://0.0.0.0:5000")
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    )