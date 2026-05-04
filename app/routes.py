from datetime import datetime, timedelta
import json

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session, current_app

from .db import get_db
from .services import compute_best_office_hours

from werkzeug.security import check_password_hash, generate_password_hash
from sqlite3 import IntegrityError
import re

main_bp = Blueprint("main", __name__)


TIME_FORMAT = "%I:%M %p"


def _get_professor_settings(db):
    """Get or create professor settings."""
    settings = db.execute("SELECT * FROM professor_settings LIMIT 1").fetchone()
    if not settings:
        db.execute("INSERT INTO professor_settings (office_hours_per_week) VALUES (2)")
        db.commit()
        settings = db.execute("SELECT * FROM professor_settings LIMIT 1").fetchone()
    return dict(settings)


def _group_slots_by_day(slots):
    days = {}
    for slot in slots:
        if "|" not in slot:
            continue
        day, time_value = slot.split("|", 1)
        days.setdefault(day, []).append(datetime.strptime(time_value, TIME_FORMAT).time())

    blocks = []
    for day, times in days.items():
        sorted_times = sorted(set(times))
        if not sorted_times:
            continue

        start = sorted_times[0]
        end = (datetime.combine(datetime.min, start) + timedelta(minutes=30)).time()

        previous = start
        for current in sorted_times[1:]:
            expected = (datetime.combine(datetime.min, previous) + timedelta(minutes=30)).time()
            if current == expected:
                previous = current
                end = (datetime.combine(datetime.min, current) + timedelta(minutes=30)).time()
            else:
                blocks.append((day, start.strftime(TIME_FORMAT), end.strftime(TIME_FORMAT)))
                start = current
                end = (datetime.combine(datetime.min, current) + timedelta(minutes=30)).time()
                previous = current

        blocks.append((day, start.strftime(TIME_FORMAT), end.strftime(TIME_FORMAT)))

    return blocks


# ---------------------------------------------------------
# NEW STUDENT ROUTES
# ---------------------------------------------------------

@main_bp.route("/")
def home():
    # Make sure this matches the name of the file you just updated!
    return render_template("index.html")

@main_bp.route("/p/<slug>", methods=["GET", "POST"])
def student_form(slug):
    db = get_db()
    
    # 1. Look up the specific professor's mailbox
    prof = db.execute("SELECT * FROM professors WHERE slug = ?", (slug,)).fetchone()
    
    if not prof:
        flash("Professor not found. Please double-check the link you were given.", "danger")
        return redirect(url_for("main.home"))
        
    if request.method == "POST":
        # Grab the student's text data
        name = request.form.get("participant_name")
        email = request.form.get("participant_email")
        
        # Grab the massive string of grid slots!
        selected_slots = request.form.get("selected_slots")
        
        if not selected_slots:
            flash("Please select at least one available time slot.", "warning")
            return redirect(url_for("main.student_form", slug=slug))

        # FEATURE: Delete any previous submissions by this student so they can safely update their hours
        db.execute("DELETE FROM student_blockouts WHERE professor_id = ? AND participant_email = ?", (prof['id'], email))
        
        # 2. Unpack the grid data (e.g., "Monday|8:00 AM,Tuesday|9:30 AM")
        from datetime import datetime, timedelta
        
        slots = selected_slots.split(',')
        for slot in slots:
            if '|' in slot:
                day, start_time = slot.split('|')
                
                # Math trick: Calculate the end time by adding 30 minutes to the start time
                start_dt = datetime.strptime(start_time, "%I:%M %p")
                end_dt = start_dt + timedelta(minutes=30)
                end_time = end_dt.strftime("%I:%M %p")
                
                # Save this specific 30-minute block to the database
                db.execute(
                    """INSERT INTO student_blockouts 
                       (professor_id, participant_name, participant_email, day, start_time, end_time, block_type) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (prof['id'], name, email, day, start_time, end_time, "Available")
                )
                
        db.commit()
        
        flash("Availability successfully submitted!", "success")
        return redirect(url_for("main.student_form", slug=slug))

    # Pass the professor's info to the HTML so we can personalize the page
    return render_template("student_form.html", professor=prof)


@main_bp.route("/admin")
def admin():
    db = get_db()

    if 'professor_id' not in session:
        flash("Please log in to view this page.", "warning")
        return redirect(url_for("main.login"))
        
    # Grab the logged-in professor's ID
    prof_id = session['professor_id']

    # --- NEW FIX 1: Fetch the full professor row from the database ---
    professor = db.execute(
        "SELECT * FROM professors WHERE id = ?", (prof_id,)
    ).fetchone()
    # -----------------------------------------------------------------

    from flask import current_app
    print(f"FLASK IS LOOKING AT: {current_app.config['DATABASE']}")

    # THE FIX: We added 'WHERE professor_id = ?' to strictly filter the mailboxes
    rows = db.execute(
        "SELECT id, participant_name, participant_email, day, start_time, end_time, block_type FROM student_blockouts WHERE professor_id = ? ORDER BY created_at DESC",
        (prof_id,)
    ).fetchall()

    student_blockouts = [dict(row) for row in rows]

    # Group submissions by participant
    submissions = {}
    for blockout in student_blockouts:
        key = (blockout['participant_name'], blockout['participant_email'])
        if key not in submissions:
            submissions[key] = {
                'participant_name': blockout['participant_name'],
                'participant_email': blockout['participant_email'],
                'availability': []
            }
        submissions[key]['availability'].append({
            'day': blockout['day'],
            'start_time': blockout['start_time'],
            'end_time': blockout['end_time'],
            'block_type': blockout['block_type']
        })

    # Convert to list and sort by most recent submission (assuming later entries are more recent)
    grouped_submissions = list(submissions.values())

    # Get professor settings
    settings = _get_professor_settings(db)
    
    # Pass settings to algorithm, catching the new dictionary response
    # Because we filtered student_blockouts above, this algorithm now ONLY runs on this specific professor's students!
    algorithm_results = compute_best_office_hours(
        student_blockouts, 
        professor_blocked_times=settings.get('professor_blocked_times', '[]'),
        office_hours_needed=settings.get('office_hours_per_week', 2)
    )

    # If the algorithm returns an empty list (no data), create a fallback dictionary
    if not algorithm_results:
        algorithm_results = {
            "schedule": [], "total_students": 0, "covered_students": 0, 
            "coverage_percentage": 0, "uncovered_list": []
        }

    return render_template(
        "admin.html", 
        professor=professor,  # <-- NEW FIX 2: Hand the professor data to the HTML!
        submissions=grouped_submissions, 
        recommendations=algorithm_results["schedule"],
        settings=settings, 
        total_students=algorithm_results["total_students"],
        covered_students=algorithm_results["covered_students"],
        coverage_percentage=algorithm_results["coverage_percentage"],
        uncovered_list=algorithm_results["uncovered_list"]
    )


@main_bp.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    db = get_db()

    if 'professor_id' not in session:
        flash("Please log in to view this page.", "warning")
        return redirect(url_for("main.login"))
        
    # Later, when you query the database, you filter by their ID!
    # Example update to your query:
    # rows = db.execute("SELECT * FROM student_blockouts WHERE professor_id = ? ORDER BY created_at DESC", (session['professor_id'],)).fetchall()

    settings = _get_professor_settings(db)
    
    if request.method == "POST":
        office_hours_per_week = int(request.form.get("office_hours_per_week", 2))
        
        # Parse blocked times from form
        blocked_times = []
        blocked_days = request.form.getlist("blocked_day")
        blocked_starts = request.form.getlist("blocked_start")
        blocked_ends = request.form.getlist("blocked_end")
        
        for i, day in enumerate(blocked_days):
            if day and i < len(blocked_starts) and i < len(blocked_ends):
                start = blocked_starts[i]
                end = blocked_ends[i]
                if start and end:
                    blocked_times.append({
                        'day': day,
                        'start_time': start,
                        'end_time': end
                    })
        
        db.execute(
            "UPDATE professor_settings SET office_hours_per_week = ?, professor_blocked_times = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (office_hours_per_week, json.dumps(blocked_times), settings['id'])
        )
        db.commit()
        
        flash("Settings saved successfully!", "success")
        return redirect(url_for("main.admin_settings"))
    
    # Parse blocked times for template
    blocked_times = []
    try:
        blocked_times = json.loads(settings.get('professor_blocked_times', '[]'))
    except:
        blocked_times = []
    
    return render_template("admin_settings.html", settings=settings, blocked_times=blocked_times)
@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower() # Good idea to keep this strip/lower!
        password = request.form.get("password")
        
        db = get_db()
        # Find the professor by email
        prof = db.execute("SELECT * FROM professors WHERE email = ?", (email,)).fetchone()
        
        print(f"DEBUG - Did it find Professor? {prof is not None}")
        if prof:
            print(f"DEBUG - Did the password match? {check_password_hash(prof['password_hash'], password)}")

        # Verify the password matches the hash
        if prof and check_password_hash(prof['password_hash'], password):
            session.clear()
            session['professor_id'] = prof['id']  # Give them their session badge!
            session['slug'] = prof['slug']        # <--- HERE IS THE NEW LINE!
            
            flash("Successfully logged in.", "success")
            return redirect(url_for("main.admin"))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template("login.html")

@main_bp.route("/logout")
def logout():
    session.clear() # Rip up the session badge
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))

@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        # 1. Generate a URL-friendly slug (e.g., "Dr. Kropp" -> "dr-kropp")
        base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        slug = base_slug

        db = get_db()

        # 2. Ensure the slug is completely unique (In case of two Dr. Smiths!)
        counter = 1
        while db.execute("SELECT id FROM professors WHERE slug = ?", (slug,)).fetchone():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # 3. Secure the password
        hashed_pw = generate_password_hash(password)

        try:
            # 4. Create the Professor account
            cursor = db.execute(
                "INSERT INTO professors (name, email, slug, password_hash) VALUES (?, ?, ?, ?)",
                (name, email, slug, hashed_pw)
            )
            prof_id = cursor.lastrowid

            # 5. Give them their default settings folder immediately
            db.execute(
                "INSERT INTO professor_settings (professor_id, office_hours_per_week) VALUES (?, ?)",
                (prof_id, 2) # Defaulting to 2 hours a week
            )
            db.commit()

            # 6. Auto-login the new user so they don't have to type it again
            session.clear()
            session['professor_id'] = prof_id
            flash(f"Welcome, {name}! Your account and unique link have been created.", "success")
            return redirect(url_for("main.admin"))

        except IntegrityError:
            # This triggers if the email UNIQUE constraint fails
            flash("An account with that email address already exists. Please log in.", "danger")
            return redirect(url_for("main.register"))

    return render_template("register.html")

# ---------------------------------------------------------
# API: LOAD STUDENT SCHEDULE
# ---------------------------------------------------------
@main_bp.route("/api/student/load")
def load_student_schedule():
    # Grabbing data safely via URL parameters instead of the URL path
    email = request.args.get('email')
    slug = request.args.get('slug')
    
    if not email or not slug:
        return jsonify({"error": "Missing data"}), 400
        
    db = get_db()
    
    # 1. Find the professor
    prof = db.execute("SELECT id FROM professors WHERE slug = ?", (slug,)).fetchone()
    if not prof:
        return jsonify({"error": "Professor not found"}), 404

    # 2. Find the student's existing blockouts
    rows = db.execute(
        "SELECT day, start_time FROM student_blockouts WHERE professor_id = ? AND lower(participant_email) = lower(?)",
        (prof['id'], email.strip())
    ).fetchall()

    # 3. Format the data for the JavaScript grid
    slots = [f"{row['day']}|{row['start_time']}" for row in rows]
    
    # 4. Grab their name
    name_row = db.execute(
        "SELECT participant_name FROM student_blockouts WHERE professor_id = ? AND lower(participant_email) = lower(?) LIMIT 1", 
        (prof['id'], email.strip())
    ).fetchone()
    
    name = name_row['participant_name'] if name_row else ""

    return jsonify({"name": name, "slots": slots})