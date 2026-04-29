-- Drop tables in reverse order of dependencies to avoid foreign key errors
DROP TABLE IF EXISTS student_blockouts;
DROP TABLE IF EXISTS professor_settings;
DROP TABLE IF EXISTS professors;

-- 1. THE NEW MASTER TABLE
CREATE TABLE professors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    slug TEXT UNIQUE NOT NULL,       -- e.g., 'dr-kropp' (used for the URL)
    password_hash TEXT NOT NULL,     -- securely store login passwords
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. UPDATED SETTINGS (Now linked to a specific professor)
CREATE TABLE professor_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER NOT NULL,   -- The crucial link back to the professor
    office_hours_per_week INTEGER DEFAULT 2,
    professor_blocked_times TEXT DEFAULT '[]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors (id) ON DELETE CASCADE
);

-- 3. UPDATED STUDENTS (Now linked to the professor they are submitting hours for)
CREATE TABLE student_blockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER NOT NULL,   -- The crucial link back to the professor
    participant_name TEXT NOT NULL,
    participant_email TEXT NOT NULL,
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    block_type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (professor_id) REFERENCES professors (id) ON DELETE CASCADE
);