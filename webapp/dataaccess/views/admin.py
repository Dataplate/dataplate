from dateutil.parser import parse as parse_date
from flask import request, render_template, flash, Blueprint, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from ..app import app, db
from ..models import *
from ..forms import RoleForm, DatasetForm, AuditLogForm, GlobalConfigForm, ServiceForm, QueryForm, UserForm
from .helpers import requires_roles, flash_errors
from ..audit import log_action
import requests, json

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/roles')
@login_required
@requires_roles('admin')
def roles():
    return render_template('roles.html', roles=Role.query.order_by(Role.name).all())


@admin.route('/role', methods=['GET', 'POST'])
@admin.route('/role/<id>', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_role(id=None):
    role = Role.query.get(int(id)) if id else Role()
    form = RoleForm(request.form, obj=role)

    if request.method == 'POST' and form.validate():
        form.populate_obj(role)
        try:
            if not id:
                db.session.add(role)
            db.session.commit()
            flash('The role has been {}!'.format('updated' if id else 'created'),
                  'success')
            log_action('role_update', str(role.to_dict()))
            return redirect(url_for('admin.roles'))
        except:
            app.logger.exception('Error updating role')
            db.session.rollback()
            flash(
                'Error {} role! Please check that the input is valid.'.format(
                    'updating' if id else 'creating'), 'danger')
        return render_template('edit_role.html', id=role.id, form=form)

    flash_errors(form)
    return render_template('edit_role.html', id=id, form=form)


@admin.route('/role/<id>/delete', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def delete_role(id):
    role = Role.query.get(int(id))
    if request.method == 'POST':
        if role.internal:
            flash('Cannot delete internal role!', 'danger')
        else:
            db.session.delete(role)
            db.session.commit()
            log_action('role_delete', role.name)
            return redirect(url_for('admin.roles'))
    return render_template('delete_role.html', role=role, form=request.form)


@admin.route('/datasets')
@login_required
@requires_roles('admin', 'harvester')
def datasets():
    return render_template('datasets.html',
                           datasets=Dataset.query.order_by(Dataset.name).all())


@admin.route('/dataset', methods=['GET', 'POST'])
@admin.route('/dataset/<id>', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'harvester')
def edit_dataset(id=None, clone=None):
    dataset = Dataset.query.get(int(id)) if id else Dataset()
    form = DatasetForm(request.form, obj=dataset)

    if request.method == 'POST' and form.validate():
        try:
            form.populate_obj(dataset)
            if not id:
                db.session.add(dataset)
            log_action('dataset_update', str(dataset.to_dict()))
            db.session.commit()
            flash('The dataset has been {}!'.format('updated' if id else 'created'),
                  'success')
            return redirect(url_for('admin.datasets'))
        except:
            app.logger.exception('Error updating dataset')
            db.session.rollback()
            flash(
                'Error {} dataset! Please check that the input is valid.'.format(
                    'updating' if id else 'creating'), 'danger')

    flash_errors(form)
    return render_template('edit_dataset.html', id=id, clone=clone, form=form)


@admin.route('/dataset/<id>/clone', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'harvester')
def clone_dataset(id):
    return edit_dataset(id=id, clone=True)


@admin.route('/dataset/<id>/delete', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'harvester')
def delete_dataset(id):
    dataset = Dataset.query.get(int(id))
    if request.method == 'POST':
        db.session.delete(dataset)
        db.session.commit()
        log_action('dataset_delete', dataset.name)
        return redirect(url_for('admin.datasets'))
    return render_template('delete_dataset.html', dataset=dataset, form=request.form)


@admin.route('/auditlog', methods=['GET'])
@login_required
@requires_roles('admin', 'auditor')
def audit_log():
    form = AuditLogForm(request.args)
    query = AuditEntry.query

    if form.validate():
        if form.from_date.data:
            query = query.filter(
                AuditEntry.created_on >= parse_date(form.from_date.data))
        if form.to_date.data:
            query = query.filter(AuditEntry.created_on <= parse_date(form.to_date.data))
        if form.query.data:
            query = query.filter(AuditEntry._fts.match(form.query.data))

    pagination = query.order_by(AuditEntry.created_on.desc()).paginate(error_out=False)

    flash_errors(form)
    return render_template('audit_log.html', pagination=pagination, form=form)


@admin.route('/config', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_config():
    config = GlobalConfig.get()
    form = GlobalConfigForm(request.form, obj=config)

    if request.method == 'POST' and form.validate():
        if request.form['submit_button'] == 'test_livy':
            # str_livy = 'livy url is: ' + str(form['livy_url'])
            validation_str = validate_livy_url(str(request.form['livy_url']))
            flash(validation_str)
        elif request.form['submit_button'] == 'actual_submit':
            form.populate_obj(config)
            if not config.id:
                db.session.add(config)
            db.session.commit()
            log_action('config_update', str(config.to_dict()))
            flash('Configuration updated', 'success')

    flash_errors(form)
    return render_template('edit_config.html', form=form)


def validate_livy_url(test_url):
    if test_url:
        try:
            host = test_url.rstrip('/')
            data = {'kind': 'spark'}
            headers = {'Content-Type': 'application/json'}
            r = requests.get(host + '/sessions', data=json.dumps(data), headers=headers, timeout=10)
            # r = requests.get(host)
            if r.status_code >=200 and r.status_code < 300:
                return('Livy connect successfuly')
            else:
                return('Failure validating your LIVY URL, make sure {}/sessions returns value and a valid status code'.format(host))
                # r.json()
                # if not website_is_up:
                #     raise ValidationError('Your Livy URL has error status: ' + status_code)
        except Exception as ex:
            return('Your Livy URL is not responding, make sure {}/sessions is accessible and not inside docker with VPN\nError: {}'.format(host,str(ex)))

@admin.route('/services')
@login_required
@requires_roles('admin')
def services():
    return render_template('services.html',
                           users=User.query.filter(User.service == True).order_by(
                               User.username).all())


@admin.route('/service', methods=['GET', 'POST'])
@admin.route('/service/<id>', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_service(id=None):
    user = User.query.get(int(id)) if id else None
    form = ServiceForm(request.form, obj=user)

    if request.method == 'POST' and form.validate():
        if user is None:
            user = User(service=True)
        user.username = form.username.data
        user.fullname = form.fullname.data
        if form.regenerate_key.data:
            user.generate_access_key()
        if not id:
            db.session.add(user)
        db.session.commit()
        flash('Service user has been {}!'.format('updated' if id else 'created'),
              'success')
        log_action('service_update', str(user.to_dict()))
        return redirect(url_for('admin.services'))

    flash_errors(form)
    return render_template('edit_service.html', id=id, form=form)


@admin.route('/service/<id>/delete', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def delete_service(id):
    user = User.query.get(int(id))
    if request.method == 'POST':
        if not user.service:
            flash('Cannot delete non-service user!', 'danger')
        else:
            db.session.delete(user)
            db.session.commit()
            log_action('service_delete', user.username)
            return redirect(url_for('admin.services'))
    return render_template('delete_service.html', user=user, form=request.form)


@admin.route('/queries')
@login_required
@requires_roles('admin', 'query-builder')
def queries():
    return render_template('queries.html',
                           queries=Query.query.order_by(Query.name).all())


@admin.route('/query', methods=['GET', 'POST'])
@admin.route('/query/<id>', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'query-builder')
def edit_query(id=None):
    query = Query.query.get(int(id)) if id else Query()
    form = QueryForm(request.form, obj=query)

    if request.method == 'POST' and form.validate():
        form.populate_obj(query)
        if not id:
            db.session.add(query)
        log_action('query_update', str(query.to_dict()))
        db.session.commit()
        flash('The query has been {}!'.format('updated' if id else 'created'),
              'success')
        return redirect(url_for('admin.queries'))

    flash_errors(form)
    return render_template('edit_query.html', id=id, form=form)


@admin.route('/query/<id>/delete', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'query-builder')
def delete_query(id):
    query = Query.query.get(int(id))
    if request.method == 'POST':
        db.session.delete(query)
        db.session.commit()
        log_action('query_delete', query.name)
        return redirect(url_for('admin.queries'))
    return render_template('delete_query.html', query=query, form=request.form)


@admin.route('/users')
@login_required
@requires_roles('admin')
def users():
    return render_template('users.html', users=User.query.order_by(User.fullname).all())


@admin.route('/user', methods=['GET', 'POST'])
@admin.route('/user/<id>', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def edit_user(id=None):
    user = User.query.get(int(id)) if id else User(editmode=True)
    form = UserForm(request.form, obj=user)

    if request.method == 'POST' and form.validate():
        form.populate_obj(user)
        try:
            user.password = generate_password_hash(user.password, method='sha256')
            if not id:
                db.session.add(user)
            db.session.commit()
            flash('The user has been {}!'.format('updated' if id else 'created'),
                  'success')
            log_action('user_update', str(user.to_dict()))
            return redirect(url_for('admin.users'))
        except:
            app.logger.exception('Error updating user')
            db.session.rollback()
            flash(
                'Error {} user! Please check that the input is valid.'.format(
                    'updating' if id else 'creating'), 'danger')
        return render_template('edit_user.html', id=user.id, form=form)

    flash_errors(form)
    return render_template('edit_user.html', id=id, form=form)


@admin.route('/user/<id>/delete', methods=['GET', 'POST'])
@login_required
@requires_roles('admin')
def delete_user(id):
    user = User.query.get(int(id))
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        log_action('user_delete', user.username)
        return redirect(url_for('admin.users'))
    return render_template('delete_user.html', user=user, form=request.form)


@admin.route('/dashboard', methods=['GET', 'POST'])
@login_required
@requires_roles('admin', 'auditor')
def dashboard():
    return render_template('dashlayout.html',dash_url='/admin/dashboard/',min_height=500)#app.index())