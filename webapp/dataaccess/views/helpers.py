from flask import abort, flash
from flask_login import current_user
from functools import wraps


def requires_roles(*roles):
    """
    View function wrapper that allows to check whether
    currently logged-in user has one of specified roles.
    """

    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if current_user.has_roles(*roles):
                return f(*args, **kwargs)
            abort(401)

        return wrapped

    return wrapper


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('{}: {}'.format(getattr(form, field).label.text, error),
                  'danger')
