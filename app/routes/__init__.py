from app.routes.auth import auth_bp
from app.routes.freelancer import freelancer_bp
from app.routes.admin import admin_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(freelancer_bp)
    app.register_blueprint(admin_bp)
