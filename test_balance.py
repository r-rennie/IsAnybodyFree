"""
Algorithm Coverage Test

This script evaluates the fairness and coverage logic of the 'compute_best_office_hours' service.
It uses highly polarized synthetic data to prove that the scheduling algorithm prioritizes 
maximizing unique student attendance over simply finding a single "most popular" time block.
"""

from app.services import compute_best_office_hours

# --- SYNTHETIC TEST COHORT ---
# These specific profiles are designed to test the algorithm's "greedy" coverage phase.
test_data = [
    # Profile 1: The Early Bird (Strict Constraint)
    # Alice represents a student with zero flexibility. If the algorithm doesn't 
    # allocate a Monday morning slot, she is entirely excluded.
    {'participant_name': 'Alice', 'participant_email': 'alice@test.com', 'day': 'Monday', 'start_time': '09:00', 'end_time': '12:00', 'block_type': 'Available'},
    
    # Profile 2: The Afternoon Worker (Orthogonal Constraint)
    # Bob's schedule has zero overlap with Alice's. This forces the algorithm 
    # to spend its "time budget" across multiple days to achieve 100% coverage.
    {'participant_name': 'Bob', 'participant_email': 'bob@test.com', 'day': 'Tuesday', 'start_time': '14:00', 'end_time': '17:00', 'block_type': 'Available'},
    
    # Profile 3: The Flexible Student (Overlap Candidate)
    # Charlie can attend during Alice's window, plus an extra day. 
    # A flawed algorithm might just schedule two blocks on Monday because it sees 
    # 2 students available then, completely ignoring Bob. A smart algorithm will 
    # group Alice and Charlie on Monday, and still save a slot for Bob on Tuesday.
    {'participant_name': 'Charlie', 'participant_email': 'charlie@test.com', 'day': 'Monday', 'start_time': '10:00', 'end_time': '14:00', 'block_type': 'Available'},
    {'participant_name': 'Charlie', 'participant_email': 'charlie@test.com', 'day': 'Wednesday', 'start_time': '10:00', 'end_time': '14:00', 'block_type': 'Available'},
]

print("Testing balanced algorithm with 3 students (different availabilities):")
print("Alice: Mon 9am-12pm | Bob: Tue 2-5pm | Charlie: Mon 10am-2pm & Wed 10am-2pm\n")

# Execute the algorithm with a budget of 3 hours.
# Given the cohort above, a successful run should return slots that cover all three 
# students without blowing past the 3-hour limit.
results = compute_best_office_hours(test_data, office_hours_needed=3)

print("Recommendations (trying to cover all students):")
for r in results['schedule']: 
    print(f"  {r['day']}: {r['start_time']}-{r['end_time']}...")