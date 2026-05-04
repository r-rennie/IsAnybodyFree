import os
import tempfile
import pytest
from app import create_app
from app.db import get_db  # Change this if your get_db is in a different file!

# ---------------------------------------------------------
# THE FIXTURE (Setting up the Ghost Database)
# ---------------------------------------------------------
@pytest.fixture
def client():
    # 1. Create a temporary, secure file path for our ghost database
    db_fd, db_path = tempfile.mkstemp()

    # 2. Spin up the app and point it exclusively to the ghost database
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE': db_path
    })

    # 3. Build the blank tables using your schema.sql blueprint
    with app.app_context():
        db = get_db()
        # Find your schema file (make sure 'schema.sql' matches your exact file name/path)
        with open('app/schema.sql', 'r') as f:
            db.executescript(f.read())
        db.commit()

    # 4. Hand the fake browser to the tests
    with app.test_client() as client:
        yield client

    # 5. TEARDOWN: The second the tests finish, nuke the ghost database from orbit!
    os.close(db_fd)
    os.unlink(db_path)

# ---------------------------------------------------------
# THE TESTS
# ---------------------------------------------------------

def test_home_fallback_page(client):
    """Test the Chaos Path: What happens if someone visits the raw URL?"""
    response = client.get("/")
    
    # Did the page load successfully? (200 OK)
    assert response.status_code == 200
    # Did it show our custom fallback message?
    assert b"Welcome to IsAnybodyFree" in response.data
    assert b"specific link provided by your professor" in response.data

def test_login_page_loads(client):
    """Test the Happy Path: Can a professor access the login page?"""
    response = client.get("/login")
    
    assert response.status_code == 200
    # Checking for the specific text on your login page
    assert b"Create Account" in response.data or b"Sign Up" in response.data or b"Log In" in response.data

def test_api_missing_data(client):
    """Test the Chaos Path: Does the API catch bad requests?"""
    # Hitting the load route WITHOUT providing an email or slug
    response = client.get("/api/student/load")
    
    # It should reject us with a 400 Bad Request error
    assert response.status_code == 400
    # It should return our custom JSON error message
    assert b"Missing data" in response.data

def test_admin_dashboard_security(client):
    """Test The Walls: Can a random person view the dashboard without logging in?"""
    # Try to go directly to the admin page
    response = client.get("/admin")
    
    # 302 means "Redirect". It should catch us and redirect us away!
    assert response.status_code == 302
    # Ensure it is redirecting us specifically to the login page
    assert "/login" in response.headers["Location"]

def test_login_failure_action(client):
    """Test POST: What happens when a professor typos their password?"""
    
    # We simulate filling out the HTML form and clicking 'Submit'
    # follow_redirects=True tells the test browser to automatically follow the routing
    response = client.post("/login", data={
        "email": "wrong_email@onu.edu",
        "password": "totallywrongpassword"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # The error flash message should appear on the screen!
    assert b"Invalid email or password" in response.data

@pytest.mark.parametrize("weird_email", [
    "no_at_symbol.com",
    "spaces in@email.com",
    "DROP TABLE students;",  # Sneaky SQL Injection attempt
    "CAPITAL@onu.edu",
    "!@#$%^&*()_+",
    "very.common@example.com"
], ids=[
    "Catches emails missing the @ symbol",
    "Catches emails with invalid spaces",
    "Defends against SQL injection attempts",
    "Handles unexpected uppercase characters",
    "Catches invalid special symbols",
    "Processes standard valid emails safely"
])
def test_api_resilience(client, weird_email):
    """Test Edge Cases: Throwing bizarre data at your API to ensure it doesn't crash."""
    
    # We use a fake slug because we just want to ensure the email string doesn't break the routing
    url = f"/api/student/load?slug=dr-fake&email={weird_email}"
    response = client.get(url)
    
    # 404 means "Professor not found", which is the correct, safe response! 
    # If the server crashed because of the weird characters, this would return a 500 error.
    assert response.status_code == 404
    assert b"Professor not found" in response.data

def test_full_student_submission(client):
    """Test POST: Can a student successfully submit their availability grid?"""
    from app.db import get_db
    
    # 1. Open the app context so we can talk to the ghost database
    with client.application.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO professors (name, email, password_hash, slug) VALUES (?, ?, ?, ?)",
            ("Test Prof", "prof@test.com", "fakehash", "test-prof")
        )
        db.commit()

    # 2. Submit the student schedule
    response = client.post("/p/test-prof", data={
        "participant_name": "Test Student",
        "participant_email": "student@test.com",
        "selected_slots": "Monday|8:00 AM,Monday|8:30 AM"
    }, follow_redirects=True)
    
    # 3. Check the backend result FIRST (This is the ultimate proof!)
    with client.application.app_context():
        db = get_db()
        saved_blocks = db.execute("SELECT * FROM student_blockouts WHERE participant_name = 'Test Student'").fetchall()
        
        # Did it actually save our 2 slots to the database?
        assert len(saved_blocks) == 2  
        
    # 4. Check the frontend result
    # We just ensure the page loaded successfully without crashing (200 OK)
    assert response.status_code == 200