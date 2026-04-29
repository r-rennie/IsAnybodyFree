"""Availability and recommendation service helpers."""

import json
from collections import defaultdict
from datetime import datetime, timedelta

def parse_time(time_str):
    """Try multiple formats to handle '09:00' and '09:00 AM'."""
    for fmt in ('%I:%M %p', '%H:%M'):
        try:
            return datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Time data '{time_str}' does not match expected formats")

def compute_best_office_hours(student_blockouts, professor_blocked_times=None, office_hours_needed=2):
    """
    Return candidate time slots based on blocked-out student availability.
    
    Algorithm limits the total scheduled duration to the requested 'office_hours_needed'.
    """
    if not student_blockouts:
        return []
    
    # Parse professor blocked times
    if professor_blocked_times is None:
        professor_blocked_times = []
    elif isinstance(professor_blocked_times, str):
        try:
            professor_blocked_times = json.loads(professor_blocked_times)
        except:
            professor_blocked_times = []
    
    # Get unique students
    students = list(set((b['participant_name'], b['participant_email']) for b in student_blockouts))
    total_students = len(students)
    
    if total_students == 0:
        return []
    
    # Group availability by student
    student_availability = defaultdict(list)
    for blockout in student_blockouts:
        if blockout['block_type'] == 'Available':
            key = (blockout['participant_name'], blockout['participant_email'])
            student_availability[key].append({
                'day': blockout['day'],
                'start': parse_time(blockout['start_time']),
                'end': parse_time(blockout['end_time'])
            })
    
    start_of_day = datetime.strptime('08:00', '%H:%M').time()
    end_of_day = datetime.strptime('20:00', '%H:%M').time()
    slot_duration = 30  # minutes
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
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
    
    candidates = []
    for day in days:
        current = start_of_day
        while current < end_of_day:
            for duration_min in [60, 90, 120]:
                block_end = (datetime.combine(datetime.min, current) + timedelta(minutes=duration_min)).time()
                if block_end > end_of_day:
                    continue
                
                is_blocked = False
                check_time = current
                while check_time < block_end:
                    if (day, check_time) in blocked_slots:
                        is_blocked = True
                        break
                    check_time = (datetime.combine(datetime.min, check_time) + timedelta(minutes=30)).time()
                
                if is_blocked:
                    continue
                
                attending_students = []
                total_overlap_minutes = 0
                min_overlap_minutes = 30

                for student_key, avail_slots in student_availability.items():
                    for avail in avail_slots:
                        if avail['day'] == day:
                            overlap_start = max(current, avail['start'])
                            overlap_end = min(block_end, avail['end'])
                            if overlap_start < overlap_end:
                                overlap_delta = datetime.combine(datetime.min, overlap_end) - datetime.combine(datetime.min, overlap_start)
                                overlap_minutes = overlap_delta.total_seconds() / 60
                                if overlap_minutes >= min_overlap_minutes:
                                    attending_students.append(student_key)
                                    total_overlap_minutes += overlap_minutes
                                    break
                
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
                            
            current = (datetime.combine(datetime.min, current) + timedelta(minutes=slot_duration)).time()
    
    if not candidates:
        return {"schedule": [], "total_students": total_students, "covered_students": 0, "uncovered_list": [], "coverage_percentage": 0}
    
    # --- BUDGET MANAGEMENT ---
    recommendations = []
    covered_students = set()
    uncovered_students = set(students)
    selected_days = set()
    
    total_minutes_scheduled = 0
    max_minutes_allowed = office_hours_needed * 60
    
    # PHASE 1: Coverage focusing on the minute budget
    while uncovered_students and candidates and total_minutes_scheduled < max_minutes_allowed:
        best_candidate = None
        best_cover_score = -1
        
        for candidate in candidates:
            # Check if this candidate would put us over budget
            if total_minutes_scheduled + candidate['duration_minutes'] > max_minutes_allowed:
                continue

            new_coverage = len(candidate['attending_students'] & uncovered_students)
            if new_coverage == 0:
                continue 
            
            day_bonus = 30.0 if candidate['day'] not in selected_days else 0
            raw_value = (new_coverage * 60) + candidate['total_overlap'] + day_bonus
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
            total_minutes_scheduled += best_candidate['duration_minutes']
            covered_students.update(best_candidate['attending_students'])
            uncovered_students -= best_candidate['attending_students']
            selected_days.add(best_candidate['day'])
            
            candidates = [c for c in candidates 
                          if c['day'] != best_candidate['day'] or 
                          len(c['attending_students'] & uncovered_students) > 0]
        else:
            break 
            
    # PHASE 2: Filling the remainder of the budget
    while total_minutes_scheduled < max_minutes_allowed and candidates:
        candidates.sort(key=lambda x: (
            -1 if x['score'] >= 0.5 else 0, 
            -(x['total_overlap'] / ((x['duration_minutes'] / 60.0) ** 0.5))
        ))
        
        best = candidates[0]
        
        # Ensure adding this doesn't exceed total hours
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
        
        # Remove conflicting slots
        candidates = [c for c in candidates if c['day'] != best['day'] or 
                      c['start_time'] >= best['end_time'] or 
                      c['end_time'] <= best['start_time']]
    
    # Sorting and Metrics
    day_order = {d: i for i, d in enumerate(days)}
    recommendations.sort(key=lambda x: (day_order.get(x['day'], 0), x['start_time']))
    
    final_covered_students_set = set()
    for rec in recommendations:
        final_covered_students_set.update(rec['attending_students'])
        del rec['attending_students'] 

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