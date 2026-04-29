import sqlite3
import os

def seed_database():
    # 100% custom, hand-picked data with 1 to 5 days of availability per student
    test_entries = [
        # 5 DAYS A WEEK (Highly Flexible)
        {"name": "Alice A.", "email": "alice@onu.edu", "day": "Monday", "start": "09:00 AM", "end": "11:00 AM"},
        {"name": "Alice A.", "email": "alice@onu.edu", "day": "Tuesday", "start": "01:00 PM", "end": "03:00 PM"},
        {"name": "Alice A.", "email": "alice@onu.edu", "day": "Wednesday", "start": "10:00 AM", "end": "12:00 PM"},
        {"name": "Alice A.", "email": "alice@onu.edu", "day": "Thursday", "start": "02:00 PM", "end": "04:30 PM"},
        {"name": "Alice A.", "email": "alice@onu.edu", "day": "Friday", "start": "08:00 AM", "end": "10:30 AM"},
        
        {"name": "Julia J.", "email": "julia@onu.edu", "day": "Monday", "start": "12:00 PM", "end": "02:00 PM"},
        {"name": "Julia J.", "email": "julia@onu.edu", "day": "Tuesday", "start": "09:30 AM", "end": "11:30 AM"},
        {"name": "Julia J.", "email": "julia@onu.edu", "day": "Wednesday", "start": "02:30 PM", "end": "04:30 PM"},
        {"name": "Julia J.", "email": "julia@onu.edu", "day": "Thursday", "start": "08:00 AM", "end": "10:00 AM"},
        {"name": "Julia J.", "email": "julia@onu.edu", "day": "Friday", "start": "01:00 PM", "end": "03:00 PM"},

        {"name": "Zane Z.", "email": "zane@onu.edu", "day": "Monday", "start": "02:00 PM", "end": "05:00 PM"},
        {"name": "Zane Z.", "email": "zane@onu.edu", "day": "Tuesday", "start": "08:30 AM", "end": "10:30 AM"},
        {"name": "Zane Z.", "email": "zane@onu.edu", "day": "Wednesday", "start": "11:00 AM", "end": "01:00 PM"},
        {"name": "Zane Z.", "email": "zane@onu.edu", "day": "Thursday", "start": "01:30 PM", "end": "03:30 PM"},
        {"name": "Zane Z.", "email": "zane@onu.edu", "day": "Friday", "start": "09:00 AM", "end": "12:00 PM"},

        # 4 DAYS A WEEK
        {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Monday", "start": "10:00 AM", "end": "12:00 PM"},
        {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Tuesday", "start": "02:00 PM", "end": "04:00 PM"},
        {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Wednesday", "start": "08:00 AM", "end": "09:30 AM"},
        {"name": "Fiona F.", "email": "fiona@onu.edu", "day": "Thursday", "start": "11:30 AM", "end": "01:30 PM"},

        {"name": "Nina N.", "email": "nina@onu.edu", "day": "Tuesday", "start": "11:00 AM", "end": "01:00 PM"},
        {"name": "Nina N.", "email": "nina@onu.edu", "day": "Wednesday", "start": "03:00 PM", "end": "05:00 PM"},
        {"name": "Nina N.", "email": "nina@onu.edu", "day": "Thursday", "start": "09:00 AM", "end": "11:00 AM"},
        {"name": "Nina N.", "email": "nina@onu.edu", "day": "Friday", "start": "02:00 PM", "end": "04:00 PM"},

        {"name": "Uma U.", "email": "uma@onu.edu", "day": "Monday", "start": "08:30 AM", "end": "10:30 AM"},
        {"name": "Uma U.", "email": "uma@onu.edu", "day": "Tuesday", "start": "01:30 PM", "end": "03:30 PM"},
        {"name": "Uma U.", "email": "uma@onu.edu", "day": "Wednesday", "start": "12:00 PM", "end": "02:00 PM"},
        {"name": "Uma U.", "email": "uma@onu.edu", "day": "Friday", "start": "10:00 AM", "end": "11:30 AM"},

        {"name": "Yara Y.", "email": "yara@onu.edu", "day": "Monday", "start": "01:00 PM", "end": "03:00 PM"},
        {"name": "Yara Y.", "email": "yara@onu.edu", "day": "Tuesday", "start": "10:00 AM", "end": "12:00 PM"},
        {"name": "Yara Y.", "email": "yara@onu.edu", "day": "Wednesday", "start": "09:00 AM", "end": "11:00 AM"},
        {"name": "Yara Y.", "email": "yara@onu.edu", "day": "Thursday", "start": "03:00 PM", "end": "05:00 PM"},

        # 3 DAYS A WEEK (Average Availability)
        {"name": "Diana D.", "email": "diana@onu.edu", "day": "Tuesday", "start": "08:00 AM", "end": "10:00 AM"},
        {"name": "Diana D.", "email": "diana@onu.edu", "day": "Thursday", "start": "12:30 PM", "end": "02:30 PM"},
        {"name": "Diana D.", "email": "diana@onu.edu", "day": "Friday", "start": "01:30 PM", "end": "03:30 PM"},

        {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Monday", "start": "11:00 AM", "end": "01:00 PM"},
        {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Wednesday", "start": "01:00 PM", "end": "03:00 PM"},
        {"name": "Hannah H.", "email": "hannah@onu.edu", "day": "Friday", "start": "09:30 AM", "end": "11:30 AM"},

        {"name": "Mike M.", "email": "mike@onu.edu", "day": "Monday", "start": "09:30 AM", "end": "11:30 AM"},
        {"name": "Mike M.", "email": "mike@onu.edu", "day": "Thursday", "start": "02:30 PM", "end": "04:30 PM"},
        {"name": "Mike M.", "email": "mike@onu.edu", "day": "Friday", "start": "11:00 AM", "end": "01:00 PM"},

        {"name": "Oscar O.", "email": "oscar@onu.edu", "day": "Monday", "start": "03:00 PM", "end": "05:00 PM"},
        {"name": "Oscar O.", "email": "oscar@onu.edu", "day": "Wednesday", "start": "08:30 AM", "end": "10:30 AM"},
        {"name": "Oscar O.", "email": "oscar@onu.edu", "day": "Friday", "start": "02:00 PM", "end": "04:00 PM"},

        {"name": "Rose R.", "email": "rose@onu.edu", "day": "Monday", "start": "08:00 AM", "end": "09:30 AM"},
        {"name": "Rose R.", "email": "rose@onu.edu", "day": "Tuesday", "start": "12:00 PM", "end": "02:00 PM"},
        {"name": "Rose R.", "email": "rose@onu.edu", "day": "Thursday", "start": "04:00 PM", "end": "05:30 PM"},

        {"name": "Steve S.", "email": "steve@onu.edu", "day": "Monday", "start": "01:30 PM", "end": "03:30 PM"},
        {"name": "Steve S.", "email": "steve@onu.edu", "day": "Wednesday", "start": "10:30 AM", "end": "12:30 PM"},
        {"name": "Steve S.", "email": "steve@onu.edu", "day": "Friday", "start": "08:30 AM", "end": "10:00 AM"},

        {"name": "Tina T.", "email": "tina@onu.edu", "day": "Tuesday", "start": "03:00 PM", "end": "05:00 PM"},
        {"name": "Tina T.", "email": "tina@onu.edu", "day": "Wednesday", "start": "01:30 PM", "end": "03:30 PM"},
        {"name": "Tina T.", "email": "tina@onu.edu", "day": "Thursday", "start": "09:30 AM", "end": "11:30 AM"},

        {"name": "Xander X.", "email": "xander@onu.edu", "day": "Wednesday", "start": "11:30 AM", "end": "01:30 PM"},
        {"name": "Xander X.", "email": "xander@onu.edu", "day": "Thursday", "start": "01:00 PM", "end": "03:00 PM"},
        {"name": "Xander X.", "email": "xander@onu.edu", "day": "Friday", "start": "03:00 PM", "end": "05:00 PM"},

        {"name": "Dan D.", "email": "dan@onu.edu", "day": "Monday", "start": "10:30 AM", "end": "12:00 PM"},
        {"name": "Dan D.", "email": "dan@onu.edu", "day": "Tuesday", "start": "02:30 PM", "end": "04:30 PM"},
        {"name": "Dan D.", "email": "dan@onu.edu", "day": "Thursday", "start": "08:00 AM", "end": "10:00 AM"},

        # 2 DAYS A WEEK
        {"name": "Charlie C.", "email": "charlie@onu.edu", "day": "Monday", "start": "02:30 PM", "end": "04:30 PM"},
        {"name": "Charlie C.", "email": "charlie@onu.edu", "day": "Wednesday", "start": "09:00 AM", "end": "10:30 AM"},

        {"name": "George G.", "email": "george@onu.edu", "day": "Wednesday", "start": "02:00 PM", "end": "04:00 PM"},
        {"name": "George G.", "email": "george@onu.edu", "day": "Friday", "start": "10:30 AM", "end": "12:30 PM"},

        {"name": "Ian I.", "email": "ian@onu.edu", "day": "Tuesday", "start": "09:00 AM", "end": "11:00 AM"},
        {"name": "Ian I.", "email": "ian@onu.edu", "day": "Thursday", "start": "02:00 PM", "end": "04:00 PM"},

        {"name": "Laura L.", "email": "laura@onu.edu", "day": "Tuesday", "start": "01:00 PM", "end": "03:00 PM"},
        {"name": "Laura L.", "email": "laura@onu.edu", "day": "Wednesday", "start": "10:00 AM", "end": "11:30 AM"},

        {"name": "Peter P.", "email": "peter@onu.edu", "day": "Tuesday", "start": "11:30 AM", "end": "01:30 PM"},
        {"name": "Peter P.", "email": "peter@onu.edu", "day": "Thursday", "start": "08:30 AM", "end": "10:30 AM"},

        {"name": "Victor V.", "email": "victor@onu.edu", "day": "Thursday", "start": "03:30 PM", "end": "05:00 PM"},
        {"name": "Victor V.", "email": "victor@onu.edu", "day": "Friday", "start": "01:00 PM", "end": "03:00 PM"},

        {"name": "Wendy W.", "email": "wendy@onu.edu", "day": "Monday", "start": "09:00 AM", "end": "10:30 AM"},
        {"name": "Wendy W.", "email": "wendy@onu.edu", "day": "Tuesday", "start": "03:30 PM", "end": "05:00 PM"},

        {"name": "Brian B.", "email": "brian@onu.edu", "day": "Monday", "start": "01:00 PM", "end": "02:30 PM"},
        {"name": "Brian B.", "email": "brian@onu.edu", "day": "Wednesday", "start": "11:00 AM", "end": "12:30 PM"},

        {"name": "Chloe C.", "email": "chloe@onu.edu", "day": "Thursday", "start": "10:00 AM", "end": "12:00 PM"},
        {"name": "Chloe C.", "email": "chloe@onu.edu", "day": "Friday", "start": "02:30 PM", "end": "04:30 PM"},

        # 1 DAY A WEEK (The "Hard Constraints")
        # If your AI algorithm is good, it will be forced to pick times inside these small windows to ensure 100% coverage.
        {"name": "Amy A.", "email": "amy@onu.edu", "day": "Tuesday", "start": "04:00 PM", "end": "05:00 PM"},
        {"name": "Bob B.", "email": "bob@onu.edu", "day": "Thursday", "start": "12:00 PM", "end": "02:00 PM"},
        {"name": "Edward E.", "email": "edward@onu.edu", "day": "Friday", "start": "03:00 PM", "end": "05:00 PM"},
        {"name": "Kevin K.", "email": "kevin@onu.edu", "day": "Monday", "start": "08:00 AM", "end": "09:30 AM"},
        {"name": "Quinn Q.", "email": "quinn@onu.edu", "day": "Wednesday", "start": "01:00 PM", "end": "02:30 PM"}
    ]

    try:
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'instance', 'app.sqlite')
        
        print(f"Connecting to: {db_path}")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("Wiping existing table (student_blockouts)...")
        cursor.execute("DELETE FROM student_blockouts")

        query = """
            INSERT INTO student_blockouts 
            (participant_name, participant_email, day, start_time, end_time, block_type)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        print(f"Inserting {len(test_entries)} fully randomized availability blocks for 30 students...")
        for s in test_entries:
            cursor.execute(query, (s['name'], s['email'], s['day'], s['start'], s['end'], "Available"))

        conn.commit()
        conn.close()
        print("Success! Database is now seeded with chaotic, real-world student data.")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"General error: {e}")

if __name__ == "__main__":
    seed_database()