"""
Database Seeding Utility

Automates the teardown and reconstruction of the local SQLite database.
Injects a baseline professor account and a diverse set of synthetic student 
availability profiles to test the scheduling algorithm's edge cases.
"""

import sqlite3
import os
from werkzeug.security import generate_password_hash

def seed_database():
    try:
        # Establish absolute paths to ensure the script targets the correct instance 
        # directory, regardless of the terminal's current working directory.
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'instance', 'app.sqlite')
        
        print(f"SEED SCRIPT IS SAVING HERE: {db_path}") 
        print(f"Connecting to: {db_path}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- PHASE 1: Schema Initialization ---
        print("Locating schema.sql...")
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
        # Directory resolution fallback: supports execution from both the 
        # project root and the inner application folder.
        path_if_root = os.path.join(base_dir, 'app', 'schema.sql')
        path_if_app = os.path.join(base_dir, 'schema.sql')
        
        if os.path.exists(path_if_root):
            schema_path = path_if_root
            print(f"-> Found schema at: {schema_path}")
        elif os.path.exists(path_if_app):
            schema_path = path_if_app
            print(f"-> Found schema at: {schema_path}")
        else:
            print(f"CRITICAL ERROR: Could not find schema.sql!")
            print(f"  Looked here: {path_if_root}")
            print(f"  Looked here: {path_if_app}")
            return # Abort execution to prevent cascading DB connection errors
            
        # Execute the Data Definition Language (DDL) to rebuild tables
        with open(schema_path, 'r') as f:
            cursor.executescript(f.read())

        # --- PHASE 2: Tenant Provisioning ---
        print("Creating Dr. Kropp account...")
        
        # Cryptographically hash the test password to simulate production-grade authentication
        hashed_pw = generate_password_hash("password123")
        cursor.execute(
            "INSERT INTO professors (name, email, slug, password_hash) VALUES (?, ?, ?, ?)",
            ("Dr. Kropp", "kropp@onu.edu", "dr-kropp", hashed_pw)
        )
        
        # Retrieve the auto-incremented primary key for foreign-key mapping
        prof_id = cursor.lastrowid

        # Initialize algorithm parameters (e.g., target 5 hours of coverage)
        cursor.execute(
            "INSERT INTO professor_settings (professor_id, office_hours_per_week) VALUES (?, ?)",
            (prof_id, 5)
        )

        # --- PHASE 3: Synthetic Data Injection ---
        # Injects varied availability patterns (from highly flexible to highly constrained)
        # to properly stress-test the scheduling algorithm's coverage logic.
        print("Inserting student data...")
        test_entries = [
            # High Flexibility (5 Days)
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Monday", "start": "09:00 AM", "end": "11:00 AM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Tuesday", "start": "01:00 PM", "end": "03:00 PM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Wednesday", "start": "10:00 AM", "end": "12:00 PM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Thursday", "start": "02:00 PM", "end": "04:30 PM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Friday", "start": "08:00 AM", "end": "10:30 AM"},
            
            # Moderate Flexibility (4 Days)
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Monday", "start": "10:00 AM", "end": "12:00 PM"},
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Tuesday", "start": "02:00 PM", "end": "04:00 PM"},
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Wednesday", "start": "08:00 AM", "end": "09:30 AM"},
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Thursday", "start": "11:30 AM", "end": "01:30 PM"},

            # Average Flexibility (3 Days)
            {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Monday", "start": "11:00 AM", "end": "01:00 PM"},
            {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Wednesday", "start": "01:00 PM", "end": "03:00 PM"},
            {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Friday", "start": "09:30 AM", "end": "11:30 AM"},

            # Low Flexibility (2 Days)
            {"name": "Ian I.", "email": "ian@onu.edu", "day": "Tuesday", "start": "09:00 AM", "end": "11:00 AM"},
            {"name": "Ian I.", "email": "ian@onu.edu", "day": "Thursday", "start": "02:00 PM", "end": "04:00 PM"},

            # Hard Constraints (Single Time Window) - The algorithm must prioritize these 
            # to achieve maximum unique student coverage.
            {"name": "Amy A.", "email": "amy@onu.edu", "day": "Tuesday", "start": "04:00 PM", "end": "05:00 PM"},
            {"name": "Bob B.", "email": "bob@onu.edu", "day": "Thursday", "start": "12:00 PM", "end": "02:00 PM"}
        ]

        query = """
            INSERT INTO student_blockouts 
            (professor_id, participant_name, participant_email, day, start_time, end_time, block_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        for s in test_entries:
            cursor.execute(query, (prof_id, s['name'], s['email'], s['day'], s['start'], s['end'], "Available"))

        conn.commit()
        conn.close()
        print("Success! Database rebuilt with Dr. Kropp and test students.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    seed_database()