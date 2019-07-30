from flask import (Blueprint, abort, current_app, flash, g, redirect,
                   render_template, request, url_for)

from OLMS.auth import admin_required, login_required, super_required
from OLMS.db import get_db
from OLMS.pagination import Pagination

bp = Blueprint('record', __name__)


@bp.route('/')
@login_required
def empl_index():
    '''Show all the records match the filter and belong the current user, most recent first.'''
    db = get_db()
    year = request.args.get('year')
    month = request.args.get('month')
    type = request.args.get('type')
    status = request.args.get('status')
    page = request.args.get('page') or 1
    per_page = request.args.get('per_page') or 10
    args = dict(year=year, month=month, type=type,
                status=status, page=page, per_page=per_page)
    years = db.execute("SELECT DISTINCT strftime('%Y', date) year FROM record"
                       ' WHERE empl_id = ? ORDER BY year DESC', (g.user['id'],)).fetchall()
    condition = ''
    if year:
        if not month:
            condition += " AND strftime('%Y', date) = '{}'".format(year)
        else:
            condition += " AND strftime('%Y%m', date) = '{}'".format(year+month)
    if type:
        condition += ' AND r.type = {}'.format(type)
    if status:
        condition += ' AND status = {}'.format(status)
    record = len(db.execute(
        'SELECT r.id, date, ABS(duration) duration, r.type, describe, d.dept_name, empl_id, realname, created, status'
        ' FROM record r JOIN employee e ON r.empl_id = e.id LEFT JOIN department d ON r.dept_id = d.id'
        ' WHERE r.empl_id = ? {}'
        ' ORDER BY created DESC'.format(condition), (g.user['id'],)).fetchall())
    limit = 'LIMIT {}, {}'.format((int(page)-1)*int(per_page), int(per_page))
    records = db.execute(
        'SELECT r.id, date, ABS(duration) duration, r.type, describe, d.dept_name, empl_id, realname, created, status'
        ' FROM record r JOIN employee e ON r.empl_id = e.id LEFT JOIN department d ON r.dept_id = d.id'
        ' WHERE r.empl_id = ? {}'
        ' ORDER BY created DESC {}'.format(condition, limit), (g.user['id'],)).fetchall()
    pagination = Pagination(per_page=int(per_page),
                            page=int(page), record=record)
    return render_template('record/index.html', records=records, years=years, args=args, pagination=pagination, mode='empl')


def admin_index(mode=None):
    db = get_db()
    dept_id = request.args.get('dept')
    empl_id = request.args.get('empl') or ''
    year = request.args.get('year')
    month = request.args.get('month')
    type = request.args.get('type')
    status = request.args.get('status')
    page = request.args.get('page') or 1
    per_page = request.args.get('per_page') or 10
    args = dict(dept_id=dept_id, empl_id=empl_id, year=year, month=month,
                type=type, status=status, page=page, per_page=per_page)
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    depts = db.execute('SELECT * FROM department'
                       ' WHERE id IN ({})'.format(','.join(permission_list))).fetchall()
    years = db.execute("SELECT DISTINCT strftime('%Y', date) year FROM record"
                       ' WHERE dept_id IN ({}) ORDER BY year DESC'.format(','.join(permission_list))).fetchall()
    if dept_id and not empl_id:
        if dept_id not in permission_list:
            abort(403)
        condition1 = 'r.dept_id = {}'.format(dept_id)
    elif empl_id:
        if str(db.execute('SELECT * FROM employee WHERE id = ?', (empl_id,)).fetchone()['dept_id']) != dept_id:
            abort(403)
        condition1 = 'empl_id = {}'.format(empl_id)
    else:
        condition1 = 'r.dept_id IN ({})'.format(','.join(permission_list))
    condition2 = ''
    if year:
        if not month:
            condition2 += " AND strftime('%Y', date) = '{}'".format(year)
        else:
            condition2 += " AND strftime('%Y%m', date) = '{}'".format(year+month)
    if type:
        condition2 += ' AND r.type = {}'.format(type)
    if status:
        condition2 += ' AND status = {}'.format(status)
    record = len(db.execute(
        'SELECT r.id, date, ABS(duration) duration, r.type, describe, d.dept_name, empl_id, realname, created, status'
        ' FROM record r JOIN employee e ON empl_id = e.id JOIN department d ON r.dept_id = d.id'
        ' WHERE {}{}'
        ' ORDER BY created DESC'.format(condition1, condition2)).fetchall())
    limit = 'LIMIT {}, {}'.format((int(page)-1)*int(per_page), int(per_page))
    records = db.execute(
        'SELECT r.id, date, ABS(duration) duration, r.type, describe, d.dept_name, empl_id, realname, created, status'
        ' FROM record r JOIN employee e ON empl_id = e.id JOIN department d ON r.dept_id = d.id'
        ' WHERE {}{}'
        ' ORDER BY created DESC {}'.format(condition1, condition2, limit)).fetchall()
    pagination = Pagination(per_page=int(per_page),
                            page=int(page), record=record)
    return render_template('record/index.html', records=records, depts=depts, years=years, args=args, pagination=pagination, mode=mode)


@bp.route('/dept')
@admin_required
def dept_index():
    '''Show all the records match the filter and belong the departments which the Administrator has
    the permission, most recent first.'''
    return admin_index(mode='dept')


@bp.route('/super')
@super_required
def super_index():
    '''Show all the records match the filter, most recent first.'''
    return admin_index(mode='super')


def get_record(id, mode='normal'):
    '''Get a record by id.

    Checks that the id exists and optionally record belong the current user or
    the department which the Administrator has the permission.

    :param id: id of record to get
    :param mode: check belongs by the current user or the Administrator
    :return: the record information
    :raise 404: if a record with the given id doesn't exist
    :raise 403: if the record not belong the current user or the Administrator
    '''
    record = get_db().execute(
        'SELECT r.id, date, ABS(duration) duration, r.type, describe, d.dept_name, empl_id, status, r.dept_id'
        ' FROM record r JOIN employee e ON r.empl_id = e.id JOIN department d ON r.dept_id = d.id'
        ' WHERE r.id = ?', (id,)).fetchone()

    if not record:
        abort(404, "Record id {0} doesn't exist.".format(id))

    if mode == 'normal':
        if record['empl_id'] != g.user['id']:
            abort(403)
    else:
        if str(record['dept_id']) not in g.user['permission'].split(','):
            abort(403)

    return record


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    '''Create a new record for the current user.'''
    if request.method == 'POST':
        ip = request.remote_addr
        date = request.form.get('date')
        error = None
        try:
            type = int(request.form.get('type'))
        except:
            error = 'Type is required.'
        try:
            if type == 1:
                duration = int(request.form.get('duration'))
                if duration < 1:
                    raise ValueError
            else:
                duration = 0 - int(request.form.get('duration'))
                if duration > -1:
                    raise ValueError
        except:
            error = 'Duration is required.'
        describe = request.form.get('describe')

        if not date:
            error = 'Date is required.'
        if g.user['id'] == 0:
            error = 'Super Administrator cannot create personal record.'

        if error:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO record (date, type, duration, describe, dept_id, empl_id, createdby)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (date, type, duration, describe, g.user['dept_id'],
                 g.user['id'], f"{g.user['id']}-{ip}"))
            db.commit()
            current_app.logger.info('UID:%s(%s)-%s create record{%s,%s,%s}',
                                    g.user['id'], g.user['realname'], ip, date, type, duration)
            return redirect(url_for('record.empl_index'))

    return render_template('record/create.html')


@bp.route('/manage/create', methods=('GET', 'POST'))
@admin_required
def manage_create():
    '''Create a new record for a employee who belong the department
    which the Administrator has the permission.'''
    db = get_db()
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    empls = db.execute(
        "SELECT e.id, dept_name || ' | ' || realname name"
        ' FROM employee e JOIN department p ON e.dept_id = p.id'
        ' WHERE p.id IN ({})'
        ' ORDER BY p.id'.format(','.join(permission_list))).fetchall()
    if request.method == 'POST':
        ip = request.remote_addr
        empl_id = request.form.get('empl')
        date = request.form.get('date')
        error = None
        try:
            type = int(request.form.get('type'))
        except:
            error = 'Type is required.'
        try:
            if type == 1:
                duration = int(request.form.get('duration'))
                if duration < 1:
                    raise ValueError
            else:
                duration = 0 - int(request.form.get('duration'))
                if duration > -1:
                    raise ValueError
        except:
            error = 'Duration is required.'
        describe = request.form.get('describe')

        if not date:
            error = 'Date is required.'
        if not empl_id:
            error = 'Employee is required.'
        empls_id = []
        for i in empls:
            empls_id.append(str(i['id']))
        if empl_id not in empls_id:
            abort(403)
        if error:
            flash(error)
        else:
            dept_id = db.execute('SELECT dept_id FROM employee WHERE id = ?',
                                 (empl_id,)).fetchone()['dept_id']
            db.execute(
                'INSERT INTO record (dept_id, empl_id, date, type, duration, describe, status, createdby, verifiedby)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (dept_id, empl_id, date, type, duration, describe,
                 1, f"{g.user['id']}-{ip}", f"{g.user['id']}-{ip}"))
            db.commit()
            current_app.logger.info('UID:%s(%s)-%s manage create record for UID:%s{%s,%s,%s}',
                                    g.user['id'], g.user['realname'], ip, empl_id, date, type, duration)
            return redirect(url_for('record.dept_index'))

    return render_template('record/create.html', empls=empls, mode='admin')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    '''Update a record by id if it belongs the current user.

    Ensures that the record is not verified.
    '''
    record = get_record(id)

    if request.method == 'POST':
        ip = request.remote_addr
        date = request.form.get('date')
        error = None
        try:
            type = int(request.form.get('type'))
        except:
            error = 'Type is required.'
        try:
            if type == 1:
                duration = int(request.form.get('duration'))
                if duration < 1:
                    raise ValueError
            else:
                duration = 0 - int(request.form.get('duration'))
                if duration > -1:
                    raise ValueError
        except:
            error = 'Duration is required.'
        describe = request.form.get('describe')

        if not date:
            error = 'Date is required.'
        if record['status'] != 0:
            error = 'You can only update record which is not verified.'

        if error:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE record SET date = ?, type = ?, duration = ?, describe = ? WHERE id = ?',
                (date, type, duration, describe, id))
            db.commit()
            current_app.logger.info('UID:%s(%s)-%s update RID:%s{%s,%s,%s}',
                                    g.user['id'], g.user['realname'], ip, id, date, type, duration)
            return redirect(url_for('record.empl_index'))

    return render_template('record/update.html', record=record)


@bp.route('/manage/<int:id>/update', methods=('GET', 'POST'))
@super_required
def manage_update(id):
    '''Update a record by Super Administrator.'''
    record = get_record(id, mode='super')
    db = get_db()
    depts = db.execute('SELECT * FROM department').fetchall()
    empls = db.execute('SELECT * FROM employee WHERE id != 0').fetchall()
    if request.method == 'POST':
        ip = request.remote_addr
        dept_id = request.form.get('dept')
        empl_id = request.form.get('empl')
        date = request.form.get('date')
        error = None
        try:
            type = int(request.form.get('type'))
        except:
            error = 'Type is required.'
        try:
            if type == 1:
                duration = int(request.form.get('duration'))
                if duration < 1:
                    raise ValueError
            else:
                duration = 0 - int(request.form.get('duration'))
                if duration > -1:
                    raise ValueError
        except:
            error = 'Duration is required.'
        status = request.form.get('status')
        describe = request.form.get('describe')

        if not empl_id:
            error = 'Employee is required.'
        if not dept_id:
            error = 'Department is required.'
        if not date:
            error = 'Date is required.'
        if not status:
            error = 'Status is required.'

        if error:
            flash(error)
        else:
            db.execute(
                'UPDATE record SET empl_id = ?, dept_id = ?, date = ?, type = ?, duration = ?, status = ?, describe = ? WHERE id = ?',
                (empl_id, dept_id, date, type, duration, status, describe, id))
            db.commit()
            current_app.logger.info('UID:%s(%s)-%s manage update RID:%s{%s,%s,%s}',
                                    g.user['id'], g.user['realname'], ip, id, date, type, duration)
            return redirect(url_for('record.super_index'))

    return render_template('record/update.html', record=record, empls=empls, depts=depts, mode='super')


@bp.route('/<int:id>/verify', methods=('GET', 'POST'))
@admin_required
def verify(id):
    '''Verify a record belong the departments which the Administrator has the permission.

    Ensures that the record is not verified.
    '''
    record = get_record(id, mode='dept')

    if request.method == 'POST':
        ip = request.remote_addr
        error = None
        if request.form.get('status') == '1':
            status = 1
        elif request.form.get('status') == '2':
            status = 2
        else:
            error = 'Unknow status.'

        if record['status'] != 0:
            error = 'The record is already verified.'
        if error:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE record SET status = ?, verifiedby = ? WHERE id = ?',
                (status, f"{g.user['id']}-{ip}", id))
            db.commit()
            current_app.logger.info(
                'UID:%s(%s)-%s verify RID:%s{%s}', g.user['id'], g.user['realname'], ip, id, status)
            return redirect(url_for('record.dept_index'))

    return render_template('record/verify.html', record=record)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    '''Delete a record by id if it belong the current user.

    Ensures that the record is not verified.
    '''
    record = get_record(id)
    ip = request.remote_addr
    error = None
    if record['status'] != 0:
        error = 'You can only delete record which is not verified.'
    if error:
        flash(error)
    else:
        db = get_db()
        db.execute('DELETE FROM record WHERE id = ?', (id,))
        db.commit()
        current_app.logger.info(
            'UID:%s(%s)-%s delete RID:%s', g.user['id'], g.user['realname'], ip, id)
        return redirect(url_for('record.empl_index'))

    return render_template('record/update.html', record=record)


@bp.route('/manage/<int:id>/delete', methods=('POST',))
@super_required
def manage_delete(id):
    '''Delete a record by Super Administrator.'''
    get_record(id, mode='super')
    ip = request.remote_addr
    db = get_db()
    db.execute('DELETE FROM record WHERE id = ?', (id,))
    db.commit()
    current_app.logger.info(
        'UID:%s(%s)-%s manage delete RID:%s', g.user['id'], g.user['realname'], ip, id)
    return redirect(url_for('record.super_index'))
