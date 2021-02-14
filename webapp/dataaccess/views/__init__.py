from .home import home
from .admin import admin
from .api import api
from ..plotlydash import bp_dash, _protect_dashviews
from ..plotlydash.dashboard import init_dashboard

def register_views(app):
    app.register_blueprint(home)
    app.register_blueprint(admin)
    app.register_blueprint(api)

    app.register_blueprint(bp_dash)
    # process dash apps
    app = init_dashboard(app, login_reg=True)