import sqlite3
import os
from werkzeug.security import generate_password_hash

def seed_database():
    try:
        # Force it to use the exact path Flask is monitoring
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'instance', 'app.sqlite')
        
        print(f"SEED SCRIPT IS SAVING HERE: {db_path}") # Make sure this print is here!
        
        print(f"Connecting to: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. WIPE AND REBUILD TABLES USING SCHEMA.SQL
        print("Locating schema.sql...")
        
        base_dir = os.path.abspath(os.path.dirname(__file__))
        
        # The script will guess both possible locations
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
            return # Stop the script so it doesn't crash later
            
        # Open and run the schema
        with open(schema_path, 'r') as f:
            cursor.executescript(f.read())

        # 2. CREATE A TEST PROFESSOR
        print("Creating Dr. Kropp account...")
        # We hash the password 'password123' so it's secure
        hashed_pw = generate_password_hash("password123")
        cursor.execute(
            "INSERT INTO professors (name, email, slug, password_hash) VALUES (?, ?, ?, ?)",
            ("Dr. Kropp", "kropp@onu.edu", "dr-kropp", hashed_pw)
        )
        
        # Grab the ID of the professor we just created (should be 1)
        prof_id = cursor.lastrowid

        # 3. GIVE DR. KROPP DEFAULT SETTINGS
        cursor.execute(
            "INSERT INTO professor_settings (professor_id, office_hours_per_week) VALUES (?, ?)",
            (prof_id, 5)
        )

        # 4. INSERT THE CHAOTIC STUDENT DATA LINKED TO DR. KROPP
        print("Inserting student data...")
        test_entries = [
            # 5 DAYS A WEEK
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Monday", "start": "09:00 AM", "end": "11:00 AM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Tuesday", "start": "01:00 PM", "end": "03:00 PM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Wednesday", "start": "10:00 AM", "end": "12:00 PM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Thursday", "start": "02:00 PM", "end": "04:30 PM"},
            {"name": "Alice A.", "email": "alice@onu.edu", "day": "Friday", "start": "08:00 AM", "end": "10:30 AM"},
            
            # 4 DAYS A WEEK
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Monday", "start": "10:00 AM", "end": "12:00 PM"},
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Tuesday", "start": "02:00 PM", "end": "04:00 PM"},
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Wednesday", "start": "08:00 AM", "end": "09:30 AM"},
            {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Thursday", "start": "11:30 AM", "end": "01:30 PM"},

            # 3 DAYS A WEEK 
            {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Monday", "start": "11:00 AM", "end": "01:00 PM"},
            {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Wednesday", "start": "01:00 PM", "end": "03:00 PM"},
            {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Friday", "start": "09:30 AM", "end": "11:30 AM"},

            # 2 DAYS A WEEK
            {"name": "Ian I.", "email": "ian@onu.edu", "day": "Tuesday", "start": "09:00 AM", "end": "11:00 AM"},
            {"name": "Ian I.", "email": "ian@onu.edu", "day": "Thursday", "start": "02:00 PM", "end": "04:00 PM"},

            # 1 DAY A WEEK (Hard Constraints)
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