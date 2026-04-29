import os
from flask import Flask


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        DATABASE=os.path.join(app.instance_path, "app.sqlite"),
        SECRET_KEY=os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production",
    )

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    from .db import close_db, init_db
    from .routes import main_bp

    app.register_blueprint(main_bp)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    return app
