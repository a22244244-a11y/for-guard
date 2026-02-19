import os
from flask import Flask


def create_app(config_class=None):
    app = Flask(__name__,
                instance_relative_config=True,
                template_folder='templates')

    if config_class is None:
        from app.config import Config
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from app.extensions import db, login_manager
    db.init_app(app)
    login_manager.init_app(app)

    from app.routes import register_blueprints
    register_blueprints(app)

    with app.app_context():
        from app.services import init_db
        init_db()

    return app
