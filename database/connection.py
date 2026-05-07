# database/connection.py
import sqlite3
import os
from config import Config
import logging

logger = logging.getLogger(__name__)


def get_db_connection():
    """Create and return a safe SQLite database connection"""

    db_path = Config.DATABASE_PATH

    try:
        # Ensure instance folder exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        conn = sqlite3.connect(
            db_path,
            timeout=10,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False
        )

        # Return rows as dictionary-like objects
        conn.row_factory = sqlite3.Row

        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")

        # Better write performance
        conn.execute("PRAGMA journal_mode=WAL")

        return conn

    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None