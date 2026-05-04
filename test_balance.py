from app.services import compute_best_office_hours

# Test with students who have different availabilities
test_data = [
    # Alice only available Monday morning
    {'participant_name': 'Alice', 'participant_email': 'alice@test.com', 'day': 'Monday', 'start_time': '09:00', 'end_time': '12:00', 'block_type': 'Available'},
    # Bob only available Tuesday afternoon
    {'participant_name': 'Bob', 'participant_email': 'bob@test.com', 'day': 'Tuesday', 'start_time': '14:00', 'end_time': '17:00', 'block_type': 'Available'},
    # Charlie available both Monday and Wednesday
    {'participant_name': 'Charlie', 'participant_email': 'charlie@test.com', 'day': 'Monday', 'start_time': '10:00', 'end_time': '14:00', 'block_type': 'Available'},
    {'participant_name': 'Charlie', 'participant_email': 'charlie@test.com', 'day': 'Wednesday', 'start_time': '10:00', 'end_time': '14:00', 'block_type': 'Available'},
]

print("Testing balanced algorithm with 3 students (different availabilities):")
print("Alice: Mon 9am-12pm, Bob: Tue 2-5pm, Charlie: Mon 10am-2pm & Wed 10am-2pm")
print()

results = compute_best_office_hours(test_data, office_hours_needed=3)
print(f"Recommendations (trying to cover all students):")

for r in results['schedule']: 
    print(f"  {r['day']}: {r['start_time']}-{r['end_time']}...")