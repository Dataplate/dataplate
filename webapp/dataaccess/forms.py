import re
import json
from dateutil.parser import parse as parse_date

from flask_wtf import FlaskForm
from wtforms import Field, TextField, TextAreaField, PasswordField, SelectField, \
        BooleanField, IntegerField
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea
from wtforms.validators import InputRequired, Required, Regexp, Length, HostnameValidation, \
        Email, URL, NumberRange, ValidationError
from wtforms.utils import unset_value

from .models import *


class MultiTextAreaField(Field):
    widget = TextArea()

    def _value(self):
        return ', '.join(sorted(self.data)) if self.data else ''

    def process(self, formdata, data=unset_value):
        if not formdata and data is not unset_value:
            self.data = data
        else:
            super(MultiTextAreaField, self).process(formdata, data)

    def process_formdata(self, valuelist):
        self.data = [
            x for x in re.split(r'[,\s]+', valuelist[0] if valuelist else '')
            if len(x) > 0
        ]


def validate_date(form, field):
    if field.data:
        try:
            parse_date(field.data)
        except ValueError:
            raise ValidationError('Unparseable date')


def validate_json(form, field):
    if field.data:
        try:
            json.loads(field.data)
        except ValueError:
            raise ValidationError('Invalid JSON')


class LoginForm(FlaskForm):
    username = EmailField('E-Mail', [InputRequired(), Email()])
    password = PasswordField('Password', [InputRequired()])


class RoleForm(FlaskForm):
    name = TextField('Name', [InputRequired()])
    description = TextField('Description', [InputRequired()])
    user_names = MultiTextAreaField('Users')
    dataset_names = MultiTextAreaField('Datasets')


class UserForm(FlaskForm):
    fullname = TextField('Full Name', [InputRequired()])
    username = TextField('Email', [InputRequired()])
    password = PasswordField('Password', [InputRequired()])
    role_names = MultiTextAreaField('Roles')
    # dataset_names = MultiTextAreaField('Datasets')

class AccessKeyForm(FlaskForm):
    access_key = TextField('Access key', [Required()])


class S3PrefixValidator(Regexp):
    def __init__(self):
        regex = r'^s3:\/\/(?P<s3_bucket>[A-Za-z0-9\-]+)(:?\/.*)$'
        message = 'Must be a valid Amazon S3 location'
        super(S3PrefixValidator, self).__init__(regex, re.IGNORECASE, message)

    def __call__(self, form, field):
        message = self.message
        match = super(S3PrefixValidator, self).__call__(form, field, message)
        # TODO: validate S3 bucket


class DatasetUrlValidator(Regexp):
    def __init__(self):
        regex = r'^jdbc:redshift:\/\/(?P<host>[^\/:]+)(:?:[0-9]+)?(:?\/.*)?|s3:\/\/(?P<s3_bucket>[A-Za-z0-9\-]+)(:?\/.*)$|^[a-zA-Z0-9-_`]+\.[a-zA-Z0-9-_`]+$'
        message = 'Must be a valid Amazon S3 location, JDBC URL or GLUE database.table'
        super(DatasetUrlValidator, self).__init__(regex, re.IGNORECASE, message)
        self.validate_hostname = HostnameValidation(require_tld=True, allow_ip=False)

    def __call__(self, form, field):
        message = self.message
        match = super(DatasetUrlValidator, self).__call__(form, field, message)
        host = match.group('host')
        if host and not self.validate_hostname(host):
            raise ValidationError(message)
        # TODO: validate S3 bucket


class DatasetForm(FlaskForm):
    TYPES = [('parquet', 'Parquet Files'), ('csv', 'CSV Files'), ('json', 'JSON Files'),
             ('redshift', 'Redshift Table'), ('glue', 'AWS Glue Table')]

    name = TextField('Name', [ \
        InputRequired(),
        Regexp('^\w+$', message="Dataset name can only contain alphanumeric and underscore characters.")
    ])
    description = TextField('Description', [InputRequired()])
    source_type = SelectField('Source type', default='parquet', choices=TYPES)
    source_url = TextField('Source URL', [InputRequired(), DatasetUrlValidator()])
    anonymized = BooleanField('Anonymized')


class AuditLogForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(AuditLogForm, self).__init__(csrf_enabled=False, *args, **kwargs)

    from_date = TextField('From date', [validate_date], id='from-date')
    to_date = TextField('To date', [validate_date], id='to-date')
    query = TextField('Text to search')


class GlobalConfigForm(FlaskForm):
    livy_url = TextField('Livy URL', [InputRequired(), URL()])
    session_wait_timeout = IntegerField(
        'Session wait timeout',
        [InputRequired(), NumberRange(0, 10000)])
    statement_wait_timeout = IntegerField(
        'Statement wait timeout',
        [InputRequired(), NumberRange(0, 100000)])
    session_name = TextField('Session name', [InputRequired(), Length(2, 100)])
    driver_memory_mb = IntegerField(
        'Driver memory (MB)',
        [InputRequired(), NumberRange(512, 20480)])
    spark_conf = TextAreaField('Spark configuration', [validate_json])
    output_path = TextField('Output Path', [InputRequired(), S3PrefixValidator()])


class ServiceForm(FlaskForm):
    username = TextField('Service name', [\
        InputRequired(),
        Regexp('^[\w\-]+$', message="Service name can only contain alphanumeric characters, underscores and hyphens.")
    ])
    fullname = TextField('Service description', [InputRequired()])
    access_key = TextField('Access key')
    regenerate_key = BooleanField('Regenerate access key')


class QueryForm(FlaskForm):
    name = TextField('Name', [ \
        InputRequired(),
        Regexp('^\w+$', message="Query name can only contain alphanumeric and underscore characters.")
    ])
    description = TextField('Description', [InputRequired()])
    sql = TextAreaField('SQL', [InputRequired()])
