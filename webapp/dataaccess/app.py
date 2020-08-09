from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

jinja_options = dict(Flask.jinja_options)
jinja_options.setdefault('extensions', []).append('jinja2_highlight.HighlightExtension')

app = Flask(__name__)
#app.secret_key = "super secret key"
app.config.from_object('dataaccess.config.Config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home.login'

from dataaccess.models import *


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


@login_manager.request_loader
def load_user_using_key(request):
    access_key = request.headers.get('X-Access-Key')
    if access_key:
        return User.query.filter_by(access_key=access_key).one_or_none()
    return None


@app.teardown_request
def teardown_request(error=None):
    from .audit import save_audit_session
    save_audit_session()


from dataaccess.views import register_views
register_views(app)
