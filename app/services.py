"""Availability and recommendation service helpers."""

import json
from collections import defaultdict
from datetime import datetime, timedelta

def parse_time(time_str):
    """
    Normalizes time strings from the frontend into usable Python time objects.
    Example: Ensures that both '09:00' and '09:00 AM' are processed correctly 
    without throwing parsing errors.
    """
    for fmt in ('%I:%M %p', '%H:%M'):
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Time data '{time_str}' does not match expected formats")

def compute_best_office_hours(student_blockouts, professor_blocked_times=None, office_hours_needed=2):
    """
    Calculates the optimal office hour schedule based on student availability.
    
    The algorithm works within a specific 'time budget' (e.g., 2 hours total) 
    and tries to maximize the number of unique students who can attend at least 
    one 30-minute block.
    """
    if not student_blockouts:
        return []
    
    # Safely load the professor's hard constraints (times they absolutely cannot meet)
    if professor_blocked_times is None:
        professor_blocked_times = []
    elif isinstance(professor_blocked_times, str):
        try:
            professor_blocked_times = json.loads(professor_blocked_times)
        except:
            professor_blocked_times = []
    
    # Identify the total pool of unique students to calculate our final coverage percentage
    students = list(set((b['participant_name'], b['participant_email']) for b in student_blockouts))
    total_students = len(students)
    
    if total_students == 0:
        return []
    
    # Reorganize the flat database rows into a dictionary grouped by student.
    # Example: student_availability[('John', 'john@email.com')] = [{Monday, 9:00, 10:00}, ...]
    student_availability = defaultdict(list)
    for blockout in student_blockouts:
        if blockout['block_type'] == 'Available':
            key = (blockout['participant_name'], blockout['participant_email'])
            student_availability[key].append({
                'day': blockout['day'],
                'start': parse_time(blockout['start_time']),
                'end': parse_time(blockout['end_time'])
            })
    
    # Define the boundaries of the search space: Monday-Friday, 8 AM to 8 PM
    start_of_day = datetime.strptime('08:00', '%H:%M').time()
    end_of_day = datetime.strptime('20:00', '%H:%M').time()
    slot_duration = 30  # We evaluate the schedule in 30-minute steps
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Pre-calculate every specific 30-minute window the professor is busy.
    # Example: If a professor blocks 1:00-2:00, we add (1:00-1:30) and (1:30-2:00) to a set for fast lookups.
    blocked_slots = set()
    for blocked in professor_blocked_times:
        if isinstance(blocked, dict):
            b_day = blocked.get('day')
            b_start = blocked.get('start_time')
            b_end = blocked.get('end_time')
            if b_day and b_start and b_end:
                b_start_t = datetime.strptime(b_start, '%H:%M').time()
                b_end_t = datetime.strptime(b_end, '%H:%M').time()
                current = b_start_t
                while current < b_end_t:
                    blocked_slots.add((b_day, current))
                    current = (datetime.combine(datetime.min, current) + timedelta(minutes=30)).time()
    
    # Step 1: Generate all possible candidate slots (60, 90, or 120 minutes long)
    candidates = []
    for day in days:
        current = start_of_day
        while current < end_of_day:
            for duration_min in [60, 90, 120]:
                block_end = (datetime.combine(datetime.min, current) + timedelta(minutes=duration_min)).time()
                
                # Discard candidates that run past 8:00 PM
                if block_end > end_of_day:
                    continue
                
                # Check if this candidate overlaps with any of the professor's blocked times
                is_blocked = False
                check_time = current
                while check_time < block_end:
                    if (day, check_time) in blocked_slots:
                        is_blocked = True
                        break
                    check_time = (datetime.combine(datetime.min, check_time) + timedelta(minutes=30)).time()
                
                if is_blocked:
                    continue
                
                # Evaluate how good this candidate is by counting student overlaps.
                # A student is counted as "attending" if they can make at least 30 minutes of this slot.
                attending_students = []
                total_overlap_minutes = 0
                min_overlap_minutes = 30

                for student_key, avail_slots in student_availability.items():
                    for avail in avail_slots:
                        if avail['day'] == day:
                            # Calculate the intersecting window between the candidate slot and the student's free time
                            overlap_start = max(current, avail['start'])
                            overlap_end = min(block_end, avail['end'])
                            
                            if overlap_start < overlap_end:
                                overlap_delta = datetime.combine(datetime.min, overlap_end) - datetime.combine(datetime.min, overlap_start)
                                overlap_minutes = overlap_delta.total_seconds() / 60
                                
                                if overlap_minutes >= min_overlap_minutes:
                                    attending_students.append(student_key)
                                    total_overlap_minutes += overlap_minutes
                                    break # Move to the next student once we confirm they can attend this block
                
                # If at least one student can attend, keep this candidate and store its metrics
                attending_count = len(attending_students)
                if attending_count > 0:
                    score = attending_count / total_students
                    candidates.append({
                        'day': day,
                        'start_time': current.strftime('%H:%M'),
                        'end_time': block_end.strftime('%H:%M'),
                        'score': score,
                        'students_available': attending_count,
                        'duration_minutes': duration_min,
                        'attending_students': set(attending_students),
                        'total_overlap': total_overlap_minutes
                    })
                            
            # Step forward by 30 minutes and try again
            current = (datetime.combine(datetime.min, current) + timedelta(minutes=slot_duration)).time()
    
    if not candidates:
        return {"schedule": [], "total_students": total_students, "covered_students": 0, "uncovered_list": [], "coverage_percentage": 0}
    
    # --- BUDGET MANAGEMENT ---
    # Convert the required hours into a minute budget (e.g., 2 hours = 120 minutes)
    recommendations = []
    covered_students = set()
    uncovered_students = set(students)
    selected_days = set()
    
    total_minutes_scheduled = 0
    max_minutes_allowed = office_hours_needed * 60
    
    # PHASE 1: Prioritize reaching the maximum number of unique students.
    # We want to avoid scheduling a time where the *same* 5 students can attend, 
    # while leaving 10 other students with no options.
    while uncovered_students and candidates and total_minutes_scheduled < max_minutes_allowed:
        best_candidate = None
        best_cover_score = -1
        
        for candidate in candidates:
            if total_minutes_scheduled + candidate['duration_minutes'] > max_minutes_allowed:
                continue

            # How many students does this slot help who haven't been helped yet?
            new_coverage = len(candidate['attending_students'] & uncovered_students)
            if new_coverage == 0:
                continue 
            
            # Add a slight bonus to slots that fall on different days to spread out availability
            day_bonus = 30.0 if candidate['day'] not in selected_days else 0
            raw_value = (new_coverage * 60) + candidate['total_overlap'] + day_bonus
            
            # Slightly penalize longer slots. This prevents blowing the whole time budget 
            # on one massive 2-hour block if two separate 1-hour blocks would serve more unique students.
            duration_factor = (candidate['duration_minutes'] / 60.0) ** 0.5 
            cover_score = raw_value / duration_factor
            
            if cover_score > best_cover_score:
                best_cover_score = cover_score
                best_candidate = candidate
        
        if best_candidate:
            recommendations.append({
                'day': best_candidate['day'],
                'start_time': best_candidate['start_time'],
                'end_time': best_candidate['end_time'],
                'score': best_candidate['score'],
                'students_available': best_candidate['students_available'],
                'duration_minutes': best_candidate['duration_minutes'],
                'attending_students': best_candidate['attending_students']
            })
            # Deduct from our budget and update our tracker sets
            total_minutes_scheduled += best_candidate['duration_minutes']
            covered_students.update(best_candidate['attending_students'])
            uncovered_students -= best_candidate['attending_students']
            selected_days.add(best_candidate['day'])
            
            # Remove candidates on the same day to enforce schedule diversity
            candidates = [c for c in candidates 
                          if c['day'] != best_candidate['day'] or 
                          len(c['attending_students'] & uncovered_students) > 0]
        else:
            break 
            
    # PHASE 2: Fill remaining time budget.
    # If everyone is covered (or impossible to cover) but we still have 30 mins of budget left,
    # pick the remaining slot with the highest general popularity.
    while total_minutes_scheduled < max_minutes_allowed and candidates:
        candidates.sort(key=lambda x: (
            -1 if x['score'] >= 0.5 else 0, 
            -(x['total_overlap'] / ((x['duration_minutes'] / 60.0) ** 0.5))
        ))
        
        best = candidates[0]
        
        if total_minutes_scheduled + best['duration_minutes'] <= max_minutes_allowed:
            recommendations.append({
                'day': best['day'],
                'start_time': best['start_time'],
                'end_time': best['end_time'],
                'score': best['score'],
                'students_available': best['students_available'],
                'duration_minutes': best['duration_minutes'],
                'attending_students': best['attending_students']
            })
            total_minutes_scheduled += best['duration_minutes']
            selected_days.add(best['day'])
        
        # Remove any candidates that overlap with the one we just selected
        candidates = [c for c in candidates if c['day'] != best['day'] or 
                      c['start_time'] >= best['end_time'] or 
                      c['end_time'] <= best['start_time']]
    
    # Prepare final output by sorting the days chronologically
    day_order = {d: i for i, d in enumerate(days)}
    recommendations.sort(key=lambda x: (day_order.get(x['day'], 0), x['start_time']))
    
    # Calculate final coverage metrics for the dashboard
    final_covered_students_set = set()
    for rec in recommendations:
        final_covered_students_set.update(rec['attending_students'])
        del rec['attending_students'] # Clean up the payload before sending to frontend

    uncovered_student_details = [
        {"name": name, "email": email} 
        for name, email in students 
        if (name, email) not in final_covered_students_set
    ]

    return {
        "schedule": recommendations,
        "total_students": total_students,
        "covered_students": len(final_covered_students_set),
        "uncovered_list": uncovered_student_details,
        "coverage_percentage": round((len(final_covered_students_set) / total_students) * 100) if total_students > 0 else 0
    }