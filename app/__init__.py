import os
from flask import Flask


def create_app():
    """
    Application Factory Pattern for the Is Anybody Free backend.
    
    This pattern dynamically generates the Flask application instance rather than 
    creating it globally. This architecture ensures better scalability, prevents 
    circular dependencies, and isolates state during unit testing.
    """
    
    # Initialize the core application, explicitly defining directories 
    # for the Jinja2 template rendering pipeline and static assets.
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Load configuration mappings.
    # The SECRET_KEY leverages the environment for secure production deployments,
    # falling back to a hardcoded string strictly for local development environments.
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "app.sqlite"),
        SECRET_KEY=os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production",
    )

    # Ensure the instance directory exists.
    # This isolates runtime-generated data (like the SQLite database file) from 
    # the version-controlled source code directory.
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Deferred imports for modular components.
    # Placed inside the factory function to avoid circular import issues 
    # when routes or database models attempt to import the 'app' instance.
    from .db import close_db, init_db
    from .routes import main_bp

    # Register the primary blueprint handling the API and view routing logic.
    app.register_blueprint(main_bp)

    # Register lifecycle hooks.
    # Binds the database connection closure to the application context teardown.
    # This guarantees that the connection pool doesn't leak memory or lock the DB 
    # after an HTTP request completes or crashes.
    app.teardown_appcontext(close_db)

    return app
