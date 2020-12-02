from flask_ldap3_login import LDAP3LoginManager, AuthenticationResponseStatus

from .app import app, db
from .models import User, Role

authenticate = None
auth_ldap = False


def init_login_backend():
    global authenticate, auth_ldap
    kind = app.config.get('LOGIN_BACKEND', 'ldap')
    if kind == 'ldap':
        ldap_manager = LDAP3LoginManager(app)
        authenticate = ldap_authenticate
        auth_ldap = True
    elif kind == 'demo':
        authenticate = demo_authenticate
    else:
        raise Exception(f'Unsupported login backend: {kind}')


def get_or_add_user(username, fullname):
    user = User.query.filter_by(username=username).one_or_none()
    if not user:
        user = User(username, fullname)
        db.session.add(user)
        db.session.commit()
    return user


def ldap_authenticate(username, password):
    response = app.ldap3_login_manager.authenticate(username, password)
    if response.status == AuthenticationResponseStatus.fail:
        raise Exception('Error authenticating with LDAP server')
    return get_or_add_user(username, response.user_info['displayName'])


def demo_authenticate(username, password):
    if username == 'demo@dataplate.io' and password == 'demo':
        user = get_or_add_user(username, 'Demo User')
        # Add the demo user to all existing roles
        if len(user.roles) == 0:
            for role in Role.query.all():
                role.user_names.append(username)
                db.session.add(role)
            db.session.commit()
        return user
    raise Exception('Wrong user/password combination!')


init_login_backend()
