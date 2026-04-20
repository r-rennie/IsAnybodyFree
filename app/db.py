import sqlite3
from pathlib import Path
from flask import current_app, g


def get_db():
    if "db" not in g:
        db_path = Path(current_app.config["DATABASE"])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf8"))
    _ensure_blockout_columns(db)


def _ensure_blockout_columns(db):
    existing = {row[1] for row in db.execute("PRAGMA table_info(student_blockouts)").fetchall()}
    if "participant_name" not in existing:
        db.execute("ALTER TABLE student_blockouts ADD COLUMN participant_name TEXT")
    if "participant_email" not in existing:
        db.execute("ALTER TABLE student_blockouts ADD COLUMN participant_email TEXT")
