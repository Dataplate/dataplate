from .home import home
from .admin import admin
from .api import api


def register_views(app):
    app.register_blueprint(home)
    app.register_blueprint(admin)
    app.register_blueprint(api)
