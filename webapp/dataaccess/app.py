import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_ldap3_login import LDAP3LoginManager
from logging.config import dictConfig

from .version import VERSION

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

jinja_options = dict(Flask.jinja_options)
jinja_options.setdefault('extensions', []).append('jinja2_highlight.HighlightExtension')

app = Flask(__name__)

# All environment variables prefixed with 'DA_' automatically appended to the application config
# (without the prefix)
app.config.update({k[3:]: v for k, v in os.environ.items() if k.startswith('DA_')})
app.config['VERSION'] = VERSION
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'home.login'

from dataaccess.login import init_login_backend
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
