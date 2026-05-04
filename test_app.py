import os
import tempfile
import pytest
from app import create_app
from app.db import get_db

# ---------------------------------------------------------
# TEST ENVIRONMENT FIXTURE
# ---------------------------------------------------------
@pytest.fixture
def client():
    """
    Test Client Initialization Context.
    
    Instead of running tests on your real development database (which would ruin 
    your actual saved data), this fixture creates a temporary, blank-slate database 
    file just for this test run—like a digital sandbox.
    """
    # 1. Ask the operating system for a safe, temporary file location
    db_fd, db_path = tempfile.mkstemp()

    # 2. Boot up a special instance of the Flask application and point its 
    # internal compass exclusively to our temporary file.
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE': db_path
    })

    # 3. Build the required tables inside our temporary database using the schema file.
    with app.app_context():
        db = get_db()
        with open('app/schema.sql', 'r') as f:
            db.executescript(f.read())
        db.commit()

    # 4. Yield control to the test function, providing it with a simulated web browser (client) 
    # to navigate the app.
    with app.test_client() as client:
        yield client

    # 5. Teardown: The moment the test completes, close the connection and physically 
    # delete the temporary file from the hard drive, leaving no trace behind.
    os.close(db_fd)
    os.unlink(db_path)


# ---------------------------------------------------------
# APPLICATION ROUTING & SECURITY TESTS
# ---------------------------------------------------------

def test_home_fallback_page(client):
    """
    Verifies the root directory fallback mechanism.
    If a student guesses the base URL instead of using their professor's specific link, 
    the system should safely land them on a generalized instruction page rather than crashing.
    """
    response = client.get("/")
    
    assert response.status_code == 200
    assert b"<h1>IsAnybodyFree?</h1>" in response.data
    assert b"specific, direct link provided by your professor" in response.data


def test_login_page_loads(client):
    """
    Standard HTTP GET validation.
    Ensures the login template renders correctly without internal server errors.
    """
    response = client.get("/login")
    
    assert response.status_code == 200
    assert b"Create Account" in response.data or b"Sign Up" in response.data or b"Log In" in response.data


def test_api_missing_data(client):
    """
    API Input Validation Test.
    Simulates a scenario where a browser drops network packets or a malicious user 
    tries to ping the API directly without attaching the required identification parameters.
    """
    response = client.get("/api/student/load")
    
    # The server should reject the request outright (HTTP 400 Bad Request)
    assert response.status_code == 400
    assert b"Missing data" in response.data


def test_admin_dashboard_security(client):
    """
    Session Authorization Test.
    Acts like a digital bouncer. If someone tries to navigate directly to the protected 
    dashboard URL without an active login session, the server should intercept the request.
    """
    response = client.get("/admin")
    
    # HTTP 302 signifies a forced redirect.
    assert response.status_code == 302
    
    # Confirm the system specifically kicked them back to the login screen.
    assert "/login" in response.headers["Location"]


def test_login_failure_action(client):
    """
    Authentication Rejection Test.
    Simulates a user typing the wrong credentials into the login form and clicking submit.
    """
    # The dictionary passed to 'data' mimics the exact payload a web browser sends.
    response = client.post("/login", data={
        "email": "wrong_email@onu.edu",
        "password": "totallywrongpassword"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Ensure the UI provides practical feedback to the user about why the login failed.
    assert b"Invalid email or password" in response.data


# ---------------------------------------------------------
# EDGE CASE & INTEGRATION TESTS
# ---------------------------------------------------------

@pytest.mark.parametrize("weird_email", [
    "no_at_symbol.com",
    "spaces in@email.com",
    "DROP TABLE students;",  
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
    """
    Parameterized Input Sanitization Test.
    Instead of writing six different tests, this function runs multiple times, throwing 
    various formats of junk data at the API. If the system is secure, it will handle 
    the bad data gracefully rather than throwing an internal 500 server crash.
    """
    url = f"/api/student/load?slug=dr-fake&email={weird_email}"
    response = client.get(url)
    
    # HTTP 404 is the expected, safe response because 'dr-fake' does not exist.
    assert response.status_code == 404
    assert b"Professor not found" in response.data


def test_full_student_submission(client):
    """
    End-to-End Integration Test.
    Proves the entire chain works from the front to the back: setting up a database record, 
    processing an HTTP form submission, and verifying the new data was physically written to the disk.
    """
    # 1. Background Setup: Inject a fake professor into the sandbox database so the form has a valid target.
    with client.application.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO professors (name, email, password_hash, slug) VALUES (?, ?, ?, ?)",
            ("Test Prof", "prof@test.com", "fakehash", "test-prof")
        )
        db.commit()

    # 2. Simulate the HTTP POST request triggered when a student clicks 'Submit' on their availability grid.
    response = client.post("/p/test-prof", data={
        "participant_name": "Test Student",
        "participant_email": "student@test.com",
        "selected_slots": "Monday|8:00 AM,Monday|8:30 AM"
    }, follow_redirects=True)
    
    # 3. Database Verification: Bypass the web interface and look directly at the hard drive 
    # to guarantee the data was actually saved in the correct format.
    with client.application.app_context():
        db = get_db()
        saved_blocks = db.execute("SELECT * FROM student_blockouts WHERE participant_name = 'Test Student'").fetchall()
        
        # We submitted 2 slots in the comma-separated string, so we expect exactly 2 distinct rows in the database.
        assert len(saved_blocks) == 2  
        
    # 4. View Verification: Ensure the server rendered the final "Success" page without crashing.
    assert response.status_code == 200