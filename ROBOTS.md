
# ROBOTS.md

## Project structure

- `app/` - core application directory (Application Factory pattern)
  - `__init__.py` - initializes Flask app and registers blueprints
  - `db.py` - database connection and initialization logic
  - `routes.py` - primary routing for admin and student views
  - `templates/` - HTML files (`index.html`, `admin.html`, `student_form.html`)
- `instance/` - contains the live SQLite database (`isanybodyfree.sqlite`)
- `requirements.txt` - Python dependency manifest (Flask, Pytest, etc.)
- `pytest.ini` - configuration for automated testing suite

## Current app state

- Production-ready Flask app deployed to **PythonAnywhere**
- Features a dynamic landing page, professor dashboard, and unique student submission links
- Live at `https://isanybodyfree.pythonanywhere.com/`

## Deployment intent

- Successfully migrated from local development to PythonAnywhere cloud hosting
- Transitioned to a "manual configuration" WSGI setup to support Application Factory architecture

## Suggested project structure

- `app/`
  - `__init__.py` - Factory initialization
  - `routes.py` - Request handling (using `main_bp` blueprint)
  - `db.py` - SQLite helper functions
  - `templates/` - UI files (Separated landing, admin, and student form views)
  - `static/` - CSS and styling assets
- `tests/` - Pytest suite for route and database validation
- `requirements.txt` - Deployment dependencies
- `ROBOTS.md` - Deployment reference and project evolution log

## Implementation plan

1. **Start small** (COMPLETED)
   - Prototype evolved from "Hello World" to a functional scheduler.
2. **Collect student availability** (COMPLETED)
   - Implemented drag-select grid for intuitive time blocking.
3. **Support multiple submissions per device** (COMPLETED)
   - Database schema uses `participant_name` and `email` to allow shared device usage.
4. **Build availability logic** (COMPLETED)
   - `compute_best_office_hours` algorithm identifies optimal slots based on student density.
5. **Improve interface to a grid-style layout** (COMPLETED)
   - Integrated full-week grid for both submission and results display.
6. **Add recommendation output** (COMPLETED)
   - Dashboard now displays top recommended windows with coverage percentages.
7. **Production Hardening** (IN PROGRESS)
   - Scrubbed hardcoded test data (e.g., `kropp@onu.edu`).
   - Refined URL generation using `url_for` with `_external=True`.
   - Separated Landing Page logic from Student Submission logic.

## Next step

- `2026-04-17` - Added SQLite persistence and drag-select grid layout.
- `2026-04-30` - Refined admin dashboard to group submissions by student.
- `2026-05-02` - **DEPLOYMENT:** Successfully launched live on PythonAnywhere.
- `2026-05-02` - Updated landing page to improve user UX/navigation.
- `2026-05-02` - Fixed dynamic slug generation for professor shareable links.
- `2026-05-02` - Scrubbed PII/test emails from codebase and updated ROBOTS.md documentation.