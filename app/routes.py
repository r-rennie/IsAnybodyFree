from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for

from .db import get_db

main_bp = Blueprint("main", __name__)


TIME_FORMAT = "%H:%M"


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

        if participant_name and participant_email and selected_slots:
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
