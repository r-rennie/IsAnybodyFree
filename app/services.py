"""Availability and recommendation service helpers."""

import json
from collections import defaultdict
from datetime import datetime, timedelta


def compute_best_office_hours(student_blockouts, professor_blocked_times=None, office_hours_needed=2):
    """
    Return candidate time slots based on blocked-out student availability.
    
    Algorithm balances:
    (a) Percentage of students available during each time slot
    (b) Ensures variety so all students can attend at least 1 slot
    
    Uses a two-phase approach:
    1. First, ensure each student is covered by at least one slot
    2. Then, fill remaining slots with highest-scoring candidates
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
                'start': datetime.strptime(blockout['start_time'], '%I:%M %p').time(),
                'end': datetime.strptime(blockout['end_time'], '%I:%M %p').time()
            })
    
    # Define the time range to search (e.g., 8 AM to 8 PM in 30-min slots)
    start_of_day = datetime.strptime('08:00', '%H:%M').time()
    end_of_day = datetime.strptime('20:00', '%H:%M').time()
    slot_duration = 30  # minutes
    
    # Days to consider
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Build set of professor blocked slots for quick lookup
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
    
    # Find all valid candidate slots (minimum 1 hour, 50%+ attendance)
    candidates = []
    
    for day in days:
        current = start_of_day
        while current < end_of_day:
            # Try block durations: 1hr, 1.5hr, 2hr (minimum 1 hour)
            for duration_min in [60, 90, 120]:
                block_end = (datetime.combine(datetime.min, current) + timedelta(minutes=duration_min)).time()
                
                if block_end > end_of_day:
                    continue
                
                # Check if this slot is blocked by professor
                is_blocked = False
                check_time = current
                while check_time < block_end:
                    if (day, check_time) in blocked_slots:
                        is_blocked = True
                        break
                    check_time = (datetime.combine(datetime.min, check_time) + timedelta(minutes=30)).time()
                
                if is_blocked:
                    continue
                
                # Find which students can attend this entire block
                attending_students = []
                for student_key, avail_slots in student_availability.items():
                    for avail in avail_slots:
                        if avail['day'] == day and avail['start'] <= current and avail['end'] >= block_end:
                            attending_students.append(student_key)
                            break
                
                attending_count = len(attending_students)
                if attending_count > 0:
                    score = attending_count / total_students
                    
                    # Include all candidates (even below 50%) to ensure coverage
                    # But prioritize 50%+ in phase 2
                    candidates.append({
                        'day': day,
                        'start_time': current.strftime('%H:%M'),
                        'end_time': block_end.strftime('%H:%M'),
                        'score': score,
                        'students_available': attending_count,
                        'duration_minutes': duration_min,
                        'attending_students': set(attending_students)
                    })
                
                break  # Only use the longest duration that works for this start time
            
            # Move to next 30-min slot
            current = (datetime.combine(datetime.min, current) + timedelta(minutes=slot_duration)).time()
    
    if not candidates:
        return []
    
    # PHASE 1: Ensure each student is covered by at least one slot
    recommendations = []
    covered_students = set()
    uncovered_students = set(students)
    
    # Track which days we've selected from
    selected_days = set()
    
    # Keep selecting until all students are covered or we run out of slots
    while uncovered_students and candidates and len(recommendations) < office_hours_needed:
        best_candidate = None
        best_cover_score = -1
        
        for candidate in candidates:
            # How many uncovered students does this candidate cover?
            new_coverage = len(candidate['attending_students'] & uncovered_students)
            
            if new_coverage == 0:
                continue  # Skip candidates that don't cover any new students
            
            # Prioritize: (1) most new students covered, (2) highest attendance score, (3) different day
            day_bonus = 2.0 if candidate['day'] not in selected_days else 0
            cover_score = (new_coverage * 10) + candidate['score'] + day_bonus
            
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
                'duration_minutes': best_candidate['duration_minutes']
            })
            covered_students.update(best_candidate['attending_students'])
            uncovered_students -= best_candidate['attending_students']
            selected_days.add(best_candidate['day'])
            
            # Remove ALL candidates on the same day that don't add new coverage
            candidates = [c for c in candidates 
                          if c['day'] != best_candidate['day'] or 
                          len(c['attending_students'] & uncovered_students) > 0]
        else:
            break  # No more candidates can cover remaining students (prefer 50%+)
    while len(recommendations) < office_hours_needed and candidates:
        # Sort remaining by score (50%+ first, then by score)
        candidates.sort(key=lambda x: (-1 if x['score'] >= 0.5 else 0, -x['score']))
        
        best = candidates[0]
        
        # Only add if it's 50%+ OR we have no better options
        if best['score'] >= 0.5 or len([c for c in candidates if c['score'] >= 0.5]) == 0:
            recommendations.append({
                'day': best['day'],
                'start_time': best['start_time'],
                'end_time': best['end_time'],
                'score': best['score'],
                'students_available': best['students_available'],
                'duration_minutes': best['duration_minutes']
            })
            selected_days.add(best['day'])
        
        candidates = candidates[1:]
    
    # Sort final recommendations by day and time for readability
    day_order = {d: i for i, d in enumerate(days)}
    recommendations.sort(key=lambda x: (day_order.get(x['day'], 0), x['start_time']))
    
    return recommendations
