"""
Application Entry Point

This script serves as the primary execution file to launch the Flask development server.
It imports the application factory from the main package and instantiates the server.
"""

from app import create_app

# Instantiate the Flask application using the factory pattern.
# This keeps the global namespace clean and ensures all configurations and blueprints 
# are loaded properly before the server starts accepting requests.
app = create_app()

# The __name__ check ensures that the development server only runs if this script 
# is executed directly (e.g., `python run.py`). It prevents the server from starting 
# accidentally if this file is ever imported as a module elsewhere in the codebase.
if __name__ == "__main__":
    # Launch the local WSGI server on port 8080.
    # debug=True enables the interactive Werkzeug debugger and auto-reloading 
    # when code changes are detected. This must be disabled in a production deployment.
    app.run(port=8080, debug=True)