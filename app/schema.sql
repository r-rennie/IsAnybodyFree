/*
  Is Anybody Free - Relational Database Schema
  
  This schema establishes a multi-tenant architecture, allowing the application 
  to host multiple professors simultaneously without data bleeding between them. 
  It utilizes strict Foreign Key constraints to maintain referential integrity.
*/

-- Idempotent Teardown Phase
-- Drops tables in reverse order of their foreign key dependencies to prevent 
-- constraint violation errors during sequential re-initialization.
DROP TABLE IF EXISTS student_blockouts;
DROP TABLE IF EXISTS professor_settings;
DROP TABLE IF EXISTS professors;


/* 1. Primary Entity: Professors
  Acts as the root node for the multi-tenant data model. All configurations 
  and student submissions cascade down from these records.
*/
CREATE TABLE professors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    
    -- Routing Identifier: Provides a secure, URL-safe string to dynamically 
    -- generate the public-facing availability forms without exposing internal database IDs.
    slug TEXT UNIQUE NOT NULL,       
    
    -- Security: Stores the cryptographic hash of the user's password, never the plaintext.
    password_hash TEXT NOT NULL,     
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


/* 2. Configuration Entity: Professor Settings
  Stores the hyperparameters and hard constraints for the scheduling algorithm.
  Maintains a 1-to-1 (or 1-to-many depending on future scaling) relationship with the professor.
*/
CREATE TABLE professor_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER NOT NULL,
    
    -- Algorithm target constraint (e.g., limit output to 2 hours)
    office_hours_per_week INTEGER DEFAULT 2,
    
    -- Hard constraints: Serialized JSON array of times the professor is strictly unavailable.
    professor_blocked_times TEXT DEFAULT '[]',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Referential Integrity: If a professor account is deleted, the database engine 
    -- automatically wipes their associated settings to prevent orphaned data.
    FOREIGN KEY (professor_id) REFERENCES professors (id) ON DELETE CASCADE
);


/* 3. Transactional Entity: Student Blockouts
  Acts as the primary search space for the algorithm. Stores the temporal availability 
  of the student cohort, strictly scoped to a specific professor's query.
*/
CREATE TABLE student_blockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_id INTEGER NOT NULL,
    participant_name TEXT NOT NULL,
    participant_email TEXT NOT NULL,
    
    -- Temporal Boundaries
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    block_type TEXT NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Referential Integrity: Ensures that if a professor leaves the platform, 
    -- all student data submitted to them is immediately and permanently purged.
    FOREIGN KEY (professor_id) REFERENCES professors (id) ON DELETE CASCADE
);