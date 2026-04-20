# ROBOTS.md

## Project structure

- `main.py` - Flask web application entrypoint
- `README.md` - project overview and usage notes
- `requirements.txt` - Python dependency manifest
- `.venv/` - local Python virtual environment (not usually committed)

## Current app state

- Minimal Flask app serving a homepage with a "Hello world" heading and a single button
- Running locally on `http://127.0.0.1:5000/`

## Deployment intent

- Target free hosting on Render for the Flask app
- Later integration of AI-driven availability analysis for office hours scheduling

## Suggested project structure

- `main.py` - app startup script
- `app/`
  - `__init__.py` - create Flask app instance
  - `routes.py` - page routes and request handling
  - `services.py` - availability calculation and recommendation logic
  - `models.py` - data structures for schedules and results
  - `templates/` - HTML templates (`index.html`)
  - `static/` - CSS, JavaScript, images
- `requirements.txt` - dependencies
- `ROBOTS.md` - project plan and structure updates
- `README.md` - usage and deployment instructions

## Implementation plan

1. Start small
   - Keep the current Flask app as a single-page prototype
   - Replace the button with a schedule entry form
2. Collect student availability
   - Let students block out class and work times by day/time
   - Use simple inputs like day selectors + start/end times
   - Store submissions in-memory first, then add lightweight persistence
3. Support multiple submissions per device
   - Add participant identity fields such as name and email
   - Save each submission with an owner field in the database
   - Do not tie entries to browser session only, so multiple people can submit from the same device
   - Optionally verify email later via confirmation token or code if desired
4. Build availability logic
   - Create a service that computes open professor slots from student blocks
   - Start with deterministic rules (e.g. time ranges with fewest conflicts)
5. Improve interface to a grid-style layout
   - Once basic submission and persistence work, upgrade the frontend to a calendar/grid view
   - A `when2meet`-style table is a good long-term UX goal
   - For now, use a form-based entry flow and show a simple availability summary first
6. Add recommendation output
   - Show the best candidate office-hour windows on the web page
   - Keep it simple: top 3 recommended times first
7. Integrate AI/ML later
   - Once schedule collection and output works, add a model layer
   - Use the existing time-slot results as model input
   - The model can learn to prefer certain days, durations, or student patterns

## Next step

- `2026-04-17` - Plan the schedule input and availability service as the next development target
- `2026-04-17` - Added schedule blockout form and in-memory student availability submission flow
- `2026-04-17` - Added SQLite persistence for student blockouts and database schema initialization
- `2026-04-17` - Updated the form to capture participant name/email so multiple people can submit from the same device
- `2026-04-17` - Replaced dropdown selectors with a drag-select availability grid like a when2meet layout
- `2026-04-17` - Removed saved submissions from the student page so the admin panel can own that view later
