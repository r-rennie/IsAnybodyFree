import json
import re
from datetime import datetime, timedelta
from sqlite3 import IntegrityError

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .services import compute_best_office_hours

# Blueprint for the primary routing module. 
# Encapsulates the application's core endpoints to maintain modularity.
main_bp = Blueprint("main", __name__)

TIME_FORMAT = "%I:%M %p"

def _get_professor_settings(db, prof_id=None):
    """
    Retrieves the configuration parameters for the scheduling algorithm.
    Falls back to system defaults (e.g., 2 office hours) if none exist.
    """
    # Note: In a multi-tenant environment, this should strictly filter by professor_id.
    # We fetch the first available settings or initialize defaults.
    settings = db.execute("SELECT * FROM professor_settings LIMIT 1").fetchone()
    if not settings:
        db.execute("INSERT INTO professor_settings (office_hours_per_week) VALUES (2)")
        db.commit()
        settings = db.execute("SELECT * FROM professor_settings LIMIT 1").fetchone()
    return dict(settings)


@main_bp.route("/")
def home():
    """Renders the landing page."""
    return render_template("index.html")


@main_bp.route("/p/<slug>", methods=["GET", "POST"])
def student_form(slug):
    """
    Public-facing endpoint for student availability submission.
    Uses URL slugs to dynamically route students to the correct professor's dataset.
    """
    db = get_db()
    
    # Resolve the professor identity via the URL slug
    prof = db.execute("SELECT * FROM professors WHERE slug = ?", (slug,)).fetchone()
    
    if not prof:
        flash("Professor not found. Please double-check the link you were given.", "danger")
        return redirect(url_for("main.home"))
        
    if request.method == "POST":
        name = request.form.get("participant_name")
        email = request.form.get("participant_email")
        selected_slots = request.form.get("selected_slots")
        
        if not selected_slots:
            flash("Please select at least one available time slot.", "warning")
            return redirect(url_for("main.student_form", slug=slug))

        # Idempotent operation: Clears existing records for this user before inserting new ones.
        # This allows students to update their availability without creating duplicate constraints.
        db.execute("DELETE FROM student_blockouts WHERE professor_id = ? AND participant_email = ?", (prof['id'], email))
        
        # Deserialize the frontend grid data (format: "Day|HH:MM AM")
        slots = selected_slots.split(',')
        for slot in slots:
            if '|' in slot:
                day, start_time = slot.split('|')
                
                # Normalize time blocks into standard 30-minute intervals for the algorithm
                start_dt = datetime.strptime(start_time, "%I:%M %p")
                end_dt = start_dt + timedelta(minutes=30)
                end_time = end_dt.strftime("%I:%M %p")
                
                db.execute(
                    """INSERT INTO student_blockouts 
                       (professor_id, participant_name, participant_email, day, start_time, end_time, block_type) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (prof['id'], name, email, day, start_time, end_time, "Available")
                )
                
        db.commit()
        flash("Availability successfully submitted!", "success")
        return redirect(url_for("main.student_form", slug=slug))

    return render_template("student_form.html", professor=prof)


@main_bp.route("/admin")
def admin():
    """
    Protected dashboard route. 
    Aggregates student constraint data, passes it to the scheduling algorithm, 
    and serves the calculated optimal office hours to the client.
    """
    db = get_db()

    if 'professor_id' not in session:
        flash("Please log in to view this page.", "warning")
        return redirect(url_for("main.login"))
        
    prof_id = session['professor_id']

    # Fetch professor metadata for UI personalization
    professor = db.execute("SELECT * FROM professors WHERE id = ?", (prof_id,)).fetchone()

    # Query all student availability constraints scoped strictly to this specific professor
    rows = db.execute(
        "SELECT id, participant_name, participant_email, day, start_time, end_time, block_type FROM student_blockouts WHERE professor_id = ? ORDER BY created_at DESC",
        (prof_id,)
    ).fetchall()

    student_blockouts = [dict(row) for row in rows]

    # Data Transformation: Group flat relational rows into structured dictionary objects by student.
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

    grouped_submissions = list(submissions.values())
    settings = _get_professor_settings(db)
    
    # Execute the core scheduling heuristic/algorithm
    algorithm_results = compute_best_office_hours(
        student_blockouts, 
        professor_blocked_times=settings.get('professor_blocked_times', '[]'),
        office_hours_needed=settings.get('office_hours_per_week', 2)
    )

    # Fallback state if the search space is empty (no students have submitted yet)
    if not algorithm_results:
        algorithm_results = {
            "schedule": [], "total_students": 0, "covered_students": 0, 
            "coverage_percentage": 0, "uncovered_list": []
        }

    return render_template(
        "admin.html", 
        professor=professor,
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
    """
    Configuration endpoint handling hard constraints (professor unavailability) 
    and algorithm parameters (target k-slots).
    """
    db = get_db()

    if 'professor_id' not in session:
        flash("Please log in to view this page.", "warning")
        return redirect(url_for("main.login"))

    settings = _get_professor_settings(db)
    
    if request.method == "POST":
        office_hours_per_week = int(request.form.get("office_hours_per_week", 2))
        
        # Aggregate dynamically added blockout fields into a JSON array
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
        
        # Serialize the hard constraints to JSON for storage
        db.execute(
            "UPDATE professor_settings SET office_hours_per_week = ?, professor_blocked_times = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (office_hours_per_week, json.dumps(blocked_times), settings['id'])
        )
        db.commit()
        
        flash("Settings saved successfully!", "success")
        return redirect(url_for("main.admin_settings"))
    
    # Deserialize blocked times for the frontend view
    try:
        blocked_times = json.loads(settings.get('professor_blocked_times', '[]'))
    except json.JSONDecodeError:
        blocked_times = []
    
    return render_template("admin_settings.html", settings=settings, blocked_times=blocked_times)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handles authentication and session initialization."""
    if request.method == "POST":
        email = request.form.get("email").strip().lower() 
        password = request.form.get("password")
        
        db = get_db()
        prof = db.execute("SELECT * FROM professors WHERE email = ?", (email,)).fetchone()

        # Cryptographic verification of the password hash
        if prof and check_password_hash(prof['password_hash'], password):
            session.clear()
            session['professor_id'] = prof['id']
            session['slug'] = prof['slug'] 
            
            flash("Successfully logged in.", "success")
            return redirect(url_for("main.admin"))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template("login.html")


@main_bp.route("/logout")
def logout():
    """Terminates the current session."""
    session.clear() 
    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles new user provisioning, password hashing, and unique slug generation 
    for routing the dynamic frontend forms.
    """
    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip().lower()
        password = request.form.get("password")

        # Sanitize the name into a URL-friendly routing slug
        base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
        slug = base_slug

        db = get_db()

        # Collision detection: append integer if slug already exists in the namespace
        counter = 1
        while db.execute("SELECT id FROM professors WHERE slug = ?", (slug,)).fetchone():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Secure password storage using salted hashing
        hashed_pw = generate_password_hash(password)

        try:
            cursor = db.execute(
                "INSERT INTO professors (name, email, slug, password_hash) VALUES (?, ?, ?, ?)",
                (name, email, slug, hashed_pw)
            )
            prof_id = cursor.lastrowid

            # Provision the initial parameter configurations for the scheduling algorithm
            db.execute(
                "INSERT INTO professor_settings (professor_id, office_hours_per_week) VALUES (?, ?)",
                (prof_id, 2)
            )
            db.commit()

            # Automatically establish the session post-registration
            session.clear()
            session['professor_id'] = prof_id
            flash(f"Welcome, {name}! Your account and unique link have been created.", "success")
            return redirect(url_for("main.admin"))

        except IntegrityError:
            # Catches database-level UNIQUE constraint violations (e.g., duplicate email)
            flash("An account with that email address already exists. Please log in.", "danger")
            return redirect(url_for("main.register"))

    return render_template("register.html")


# ---------------------------------------------------------
# API: LOAD STUDENT SCHEDULE
# ---------------------------------------------------------
@main_bp.route("/api/student/load")
def load_student_schedule():
    """
    RESTful endpoint for client-side hydration.
    Allows returning students to view and modify their previously submitted availability grid.
    """
    email = request.args.get('email')
    slug = request.args.get('slug')
    
    if not email or not slug:
        return jsonify({"error": "Missing data"}), 400
        
    db = get_db()
    
    # Validate authorization context via the slug
    prof = db.execute("SELECT id FROM professors WHERE slug = ?", (slug,)).fetchone()
    if not prof:
        return jsonify({"error": "Professor not found"}), 404

    # Query existing constraint state
    rows = db.execute(
        "SELECT day, start_time FROM student_blockouts WHERE professor_id = ? AND lower(participant_email) = lower(?)",
        (prof['id'], email.strip())
    ).fetchall()

    # Format into the pipe-delimited schema expected by the frontend JavaScript
    slots = [f"{row['day']}|{row['start_time']}" for row in rows]
    
    name_row = db.execute(
        "SELECT participant_name FROM student_blockouts WHERE professor_id = ? AND lower(participant_email) = lower(?) LIMIT 1", 
        (prof['id'], email.strip())
    ).fetchone()
    
    name = name_row['participant_name'] if name_row else ""

    return jsonify({"name": name, "slots": slots})