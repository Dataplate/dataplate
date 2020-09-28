import random
import string
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON, TSVECTOR
from sqlalchemy.ext.associationproxy import association_proxy
from flask_login import UserMixin

from .app import db, app


class SerializerMixin:
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True))

role_datasets = db.Table(
    'role_datasets',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('dataset_id', db.Integer, db.ForeignKey('datasets.id'), primary_key=True))


class GlobalConfig(db.Model, SerializerMixin):
    __tablename__ = 'global_config'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    livy_url = db.Column(db.String())
    session_wait_timeout = db.Column(db.Integer(), default=60)
    statement_wait_timeout = db.Column(db.Integer(), default=10 * 60 * 60)
    session_name = db.Column(db.String(100), default='DataAccess')
    spark_conf = db.Column(JSON, default='''{"spark.sql.shuffle.partitions": "25"}''')
    driver_memory_mb = db.Column(db.Integer(), default=4096)

    @staticmethod
    def get():
        config = GlobalConfig.query.one_or_none()
        if config is None:
            config = GlobalConfig()
            db.session.add(config)
            db.session.flush()
        return config


class User(db.Model, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    username = db.Column(db.String(), unique=True)
    fullname = db.Column(db.String())
    access_key = db.Column(db.String(32), unique=True)
    service = db.Column(db.Boolean(), default=False)
    roles = db.relationship('Role',
                            secondary=user_roles,
                            lazy='subquery',
                            backref=db.backref('users', lazy=True))
    audit_sessions = db.relationship('AuditSession', backref='user', lazy='dynamic')
    livy_session = db.relationship('LivySession',
                                   uselist=False,
                                   backref=db.backref('users'))

    def __init__(self, username=None, fullname=None, service=False):
        self.username = username
        self.fullname = fullname
        self.service = service
        self.generate_access_key()

    def generate_access_key(self):
        self.access_key = ''.join(
            [random.choice(string.ascii_letters + string.digits) for n in range(32)])
        from .audit import log_action
        log_action('generate_key')

    def has_roles(self, *roles):
        """
        Checks whether this user has one of specified roles
        """
        for role in roles:
            if role in [r.name for r in self.roles]:
                return True
        return False

    def main_role_name(self):
        if len(self.roles) == 0:
            return 'User'
        role_name = self.roles[0].name
        return role_name.replace('-', ' ').capitalize()


class Dataset(db.Model, SerializerMixin):
    __tablename__ = 'datasets'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    name = db.Column(db.String(), unique=True)
    description = db.Column(db.String())
    source_type = db.Column(db.String(20))
    source_url = db.Column(db.String())
    anonymized = db.Column(db.Boolean(), default=False)

    def accessible_by(self, user):
        return self.anonymized or self.query.filter(Dataset.name == self.name).join(
            Role.datasets).filter(Role.users.contains(user)).count() > 0


class Role(db.Model, SerializerMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    name = db.Column(db.String(), unique=True)
    description = db.Column(db.String())
    internal = db.Column(db.Boolean(), default=False)
    datasets = db.relationship('Dataset',
                               secondary=role_datasets,
                               lazy='subquery',
                               backref=db.backref('roles', lazy=True))
    user_names = association_proxy(
        'users',
        'username',
        creator=lambda n: User.query.filter_by(username=n).one_or_none())
    dataset_names = association_proxy(
        'datasets',
        'name',
        creator=lambda n: Dataset.query.filter_by(name=n).one_or_none())

    def to_dict(self):
        d = super(Role, self).to_dict()
        d['users'] = self.user_names
        d['datasets'] = self.dataset_names
        return d


class AuditSession(db.Model):
    __tablename__ = 'audit_sessions'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    remote_ip = db.Column(db.String(16))
    entries = db.relationship('AuditEntry', backref='session', lazy='dynamic')


class AuditEntry(db.Model):
    __tablename__ = 'audit_entries'

    __table_args__ = (
        db.Index('fts_idx', '_fts', postgresql_using='gin'),
        db.Index('created_on_idx', 'created_on'),
    )

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.Integer, db.ForeignKey('audit_sessions.id'))
    user = db.Column(db.String())
    kind = db.Column(db.String(20))
    text = db.Column(db.String())
    _fts = db.Column(TSVECTOR)


class LivySession(db.Model, SerializerMixin):
    __tablename__ = 'livy_sessions'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    livy_id = db.Column(db.Integer)
    info = db.Column(JSON)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


class Query(db.Model, SerializerMixin):
    __tablename__ = 'queries'

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime,
                           default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    name = db.Column(db.String(), unique=True)
    description = db.Column(db.String())
    sql = db.Column(db.String())
