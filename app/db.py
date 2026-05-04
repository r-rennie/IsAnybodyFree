import sqlite3
from pathlib import Path
from flask import current_app, g


def get_db():
    """
    Retrieves or establishes a database connection for the current Flask request context.
    
    This uses the Application Context 'g' object as a request-local singleton. 
    By storing the connection in 'g', we ensure that multiple internal database 
    calls during a single HTTP request reuse the same connection rather than 
    opening and closing multiple threads, which improves performance and prevents locks.
    """

    if "db" not in g:
        db_path = Path(current_app.config["DATABASE"])

        # Ensure the directory structure exists before attempting connection
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES)

        # Override the default tuple factory with sqlite3.Row.
        # This allows dictionary-like access by column name (e.g., row['start_time']),
        # making it much cleaner to parse data structures into your scheduling algorithm.
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """
    Context teardown handler.
    Safely terminates the SQLite connection when the HTTP request finishes or crashes.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Idempotent initialization script for setting up the baseline schema.
    Typically called via a Flask CLI command during deployment or first-time setup.
    """
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    _ensure_blockout_columns(db)


def _ensure_blockout_columns(db):
    """
    Lightweight, dynamic schema evolution (migration) function.
    
    Instead of relying on a heavy migration framework like Alembic for a smaller project,
    this queries SQLite's internal PRAGMA table to check current table state and 
    conditionally injects new columns if they are missing from earlier deployments.
    """
    # Extract a set of existing column names from the student_blockouts table
    existing = {row[1] for row in db.execute("PRAGMA table_info(student_blockouts)").fetchall()}
    if "participant_name" not in existing:
        db.execute("ALTER TABLE student_blockouts ADD COLUMN participant_name TEXT")
    if "participant_email" not in existing:
        db.execute("ALTER TABLE student_blockouts ADD COLUMN participant_email TEXT")
