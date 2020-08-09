from flask import g, request
from flask_login import current_user

from .app import db, app
from .models import *


def log_action(kind, text=None):
    """
    Creates a new user audit session if it doesn't exist yet,
    and adds a new log entry to it.
    """
    if current_user.is_authenticated:
        audit_session = getattr(g, 'audit_session', None)
        if audit_session is None:
            g.audit_session = audit_session = AuditSession(
                user=current_user, remote_ip=request.remote_addr)
        audit_session.entries.append(
            AuditEntry(user=current_user.username, kind=kind, text=text))


def save_audit_session():
    """
    Saves existing user audit session
    """
    audit_session = getattr(g, 'audit_session', None)
    if audit_session is not None and audit_session.entries.count() > 0:
        db.session.add(audit_session)
        db.session.commit()
