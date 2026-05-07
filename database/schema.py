# database/schema.py

import sqlite3
import logging
from config import Config

logger = logging.getLogger(__name__)


def create_tables():
    """Create all required tables if they don't exist"""

    conn = None  # ✅ Initialize to None to prevent NameError

    try:
        conn = sqlite3.connect(Config.DATABASE_PATH)
        cursor = conn.cursor()

        # ---------------- STUDENTS TABLE ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                father_name TEXT,
                department TEXT,
                year INTEGER,
                semester INTEGER,
                mobile_number TEXT,
                face_encoding BLOB NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ---------------- ATTENDANCE TABLE ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status TEXT DEFAULT 'Present',
                UNIQUE(student_id, date),
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')

        # ---------------- ADMIN TABLE ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                must_change_password INTEGER DEFAULT 1
            )
        ''')

        # ---------------- HOLIDAYS TABLE ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                reason TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ---------------- ALUMNI TABLE ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alumni (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                father_name TEXT,
                department TEXT NOT NULL,
                mobile_number TEXT,
                year INTEGER,
                passing_semester INTEGER,
                passing_year INTEGER NOT NULL,
                graduated_on TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ---------------- PROMOTION LOG TABLE ----------------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS promotion_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                promoted_on TEXT NOT NULL,
                total_promoted INTEGER DEFAULT 0,
                total_graduated INTEGER DEFAULT 0,
                promoted_by TEXT NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ---------------- INDEXES ----------------
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_attendance_date '
            'ON attendance(date)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_attendance_student '
            'ON attendance(student_id)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_students_dept '
            'ON students(department)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_students_year '
            'ON students(year)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_alumni_dept '
            'ON alumni(department)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_alumni_year '
            'ON alumni(passing_year)'
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS idx_promotion_log_date '
            'ON promotion_log(promoted_on)'
        )

        conn.commit()
        logger.info("Database tables created successfully.")

        # ---------------- MIGRATIONS ----------------
        # SQLite can't ALTER NOT NULL constraints easily; we only add columns.
        # Ensure `is_active` exists for older DBs.
        try:
            cols = {
                row[1] for row in cursor.execute("PRAGMA table_info(students)")
            }
            if "is_active" not in cols:
                cursor.execute(
                    "ALTER TABLE students ADD COLUMN is_active INTEGER DEFAULT 1"
                )
                conn.commit()
                logger.info("Migration applied: students.is_active added.")
        except Exception as e:
            logger.warning(f"Migration check failed: {e}")

        # Ensure `must_change_password` exists for older DBs.
        try:
            admin_cols = {
                row[1] for row in cursor.execute("PRAGMA table_info(admin)")
            }
            if "must_change_password" not in admin_cols:
                cursor.execute(
                    "ALTER TABLE admin ADD COLUMN must_change_password "
                    "INTEGER DEFAULT 1"
                )
                conn.commit()
                logger.info("Migration applied: admin.must_change_password added.")
        except Exception as e:
            logger.warning(f"Admin migration check failed: {e}")

    except sqlite3.Error as e:
        logger.error(f"Table creation error: {e}")

    finally:
        # ✅ Safe close — won't crash if conn failed
        if conn:
            conn.close()


if __name__ == "__main__":
    create_tables()