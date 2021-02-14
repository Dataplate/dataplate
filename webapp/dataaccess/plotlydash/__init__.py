from flask import Blueprint
from flask_login import login_required

bp_dash = Blueprint('dashboard', __name__, template_folder='../templates', url_prefix='/admin/dashboard/')

def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])