CREATE TABLE IF NOT EXISTS student_blockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_name TEXT,
    participant_email TEXT,
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    block_type TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
