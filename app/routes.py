from datetime import datetime, timedelta
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash

from .db import get_db
from .services import compute_best_office_hours

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


@main_bp.route("/", methods=["GET", "POST"])
def home():
    db = get_db()

    if request.method == "POST":
        participant_name = request.form.get("participant_name")
        participant_email = request.form.get("participant_email")
        selected_slots = request.form.get("selected_slots", "")

        if participant_name and participant_email:
            # Delete existing entries for this email
            db.execute("DELETE FROM student_blockouts WHERE participant_email = ?", (participant_email,))
            
            if selected_slots:
                slots = [s for s in selected_slots.split(",") if s]
                for day, start_time, end_time in _group_slots_by_day(slots):
                    db.execute(
                        "INSERT INTO student_blockouts (participant_name, participant_email, day, start_time, end_time, block_type) VALUES (?, ?, ?, ?, ?, ?)",
                        (participant_name, participant_email, day, start_time, end_time, "Available"),
                    )
            db.commit()

        return redirect(url_for("main.home"))

    rows = db.execute(
        "SELECT id, participant_name, participant_email, day, start_time, end_time, block_type FROM student_blockouts ORDER BY created_at DESC"
    ).fetchall()

    student_blockouts = [dict(row) for row in rows]
    return render_template("index.html", student_blockouts=student_blockouts)


@main_bp.route("/admin")
def admin():
    db = get_db()

    from flask import current_app
    print(f"FLASK IS LOOKING AT: {current_app.config['DATABASE']}")

    rows = db.execute(
        "SELECT id, participant_name, participant_email, day, start_time, end_time, block_type FROM student_blockouts ORDER BY created_at DESC"
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
        submissions=grouped_submissions, 
        recommendations=algorithm_results["schedule"],
        settings=settings, 
        total_students=algorithm_results["total_students"],
        covered_students=algorithm_results["covered_students"],
        coverage_percentage=algorithm_results["coverage_percentage"],
        uncovered_list=algorithm_results["uncovered_list"] # NEW
    )


@main_bp.route("/admin/settings", methods=["GET", "POST"])
def admin_settings():
    db = get_db()
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
