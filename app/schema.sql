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

CREATE TABLE IF NOT EXISTS professor_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    office_hours_per_week INTEGER DEFAULT 2,
    professor_blocked_times TEXT DEFAULT '[]',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
