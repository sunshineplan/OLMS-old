from flask import (Blueprint, abort, current_app, flash, g, redirect,
                   render_template, request, url_for, jsonify)
from werkzeug.security import generate_password_hash

from OLMS.auth import admin_required, super_required
from OLMS.db import get_db
from OLMS.pagination import Pagination

bp = Blueprint('empl', __name__, url_prefix='/manage/empl')


@bp.route('')
@admin_required
def index():
    '''Show all employees match the filter and belong the departments which the Administrator has the permission.'''
    db = get_db()
    dept_id = request.args.get('dept')
    type = request.args.get('type')
    page = request.args.get('page') or 1
    per_page = request.args.get('per_page') or 10
    args = dict(dept_id=dept_id, type=type, page=page, per_page=per_page)
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    depts = db.execute(
        'SELECT * FROM department WHERE id IN ({})'.format(','.join(permission_list))).fetchall()
    condition = ''
    if dept_id and dept_id != '':
        if str(dept_id) not in permission_list:
            abort(403)
        condition += 'e.dept_id = {}'.format(dept_id)
    else:
        condition += 'e.dept_id IN ({})'.format(','.join(permission_list))
    if type and type != '':
        condition += ' AND type = {}'.format(type)
    else:
        condition += ''
    record = len(db.execute(
        'SELECT e.*, dept_name FROM employee e'
        ' JOIN department d ON e.dept_id = d.id'
        ' WHERE {}'.format(condition)).fetchall())
    limit = 'LIMIT {}, {}'.format((int(page)-1)*int(per_page), int(per_page))
    empls = db.execute(
        'SELECT e.*, dept_name FROM employee e'
        ' JOIN department d ON e.dept_id = d.id'
        ' WHERE {} {}'.format(condition, limit)).fetchall()
    pagination = Pagination(per_page=int(per_page),
                            page=int(page), record=record)
    return render_template('empl/index.html', empls=empls, depts=depts, args=args, pagination=pagination)


def get_empl(id):
    '''Get a employee by id.

    Checks that the id exists.

    :param id: id of post to get
    :return: the employee information
    :raise 404: if a employee with the given id doesn't exist
    '''
    db = get_db()
    empl = db.execute('SELECT * FROM employee WHERE id = ?', (id,)).fetchone()

    if empl is None:
        abort(404, "Employee id {0} doesn't exist.".format(id))

    return empl


@bp.route('/get', methods=('POST',))
@admin_required
def get():
    dept_id = request.form.get('dept')
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    if dept_id not in permission_list:
        abort(403)
    db = get_db()
    empl = db.execute(
        'SELECT id, realname FROM employee where dept_id = ?', (dept_id,)).fetchall()
    empl = dict((i['id'], i['realname']) for i in empl)
    return jsonify(empl)


@bp.route('/add', methods=('GET', 'POST'))
@admin_required
def add():
    '''Add a new employee.

    Validates that the username is not already taken. Default password is 123456
    and hashes the password for security.
    '''
    db = get_db()
    depts = []
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    depts = db.execute(
        'SELECT * FROM department where id IN ({})'.format(','.join(permission_list))).fetchall()
    if request.method == 'POST':
        ip = request.remote_addr
        username = request.form.get('username').strip()
        realname = request.form.get('realname').strip()
        if realname == '':
            realname = username
        dept_id = request.form.get('dept')
        db = get_db()
        error = None

        if not username:
            error = 'Username is required.'
        if db.execute('SELECT id FROM employee WHERE username = ?',
                      (username,)).fetchone() is not None:
            error = 'Username {0} is already existed.'.format(username)
        if not dept_id:
            error = 'Department is required.'

        if g.user['id'] == 0:
            type = request.form.get('type')
            permission = ','.join(request.form.getlist('permission'))
            if not type:
                error = 'Type is required.'
            if type == '1' and permission == '':
                error = 'At least one permission must be selected for Administrator.'

        if error is None:
            # the name is available, store it in the database
            if g.user['id'] != 0:
                db.execute(
                    'INSERT INTO employee (username, realname, dept_id) VALUES (?, ?, ?)',
                    (username, realname, dept_id))
            else:
                db.execute(
                    'INSERT INTO employee (username, realname, dept_id, type, permission)'
                    ' VALUES (?, ?, ?, ?, ?)',
                    (username, realname, dept_id, type, permission))
            db.commit()
            current_app.logger.info(
                'UID:%s(%s)-%s add user{%s,%s,%s}', g.user['id'], g.user['realname'], ip, username, realname, dept_id)
            return redirect(url_for('empl.index'))

        flash(error)

    return render_template('empl/add.html', depts=depts)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@super_required
def update(id):
    '''Update a employee by id.

    Ensures that the employee exists.
    '''
    empl = get_empl(id)
    try:
        permission_list = list(map(int, empl['permission'].split(',')))
    except ValueError:
        permission_list = []
    db = get_db()
    depts = db.execute('SELECT * from department').fetchall()
    if request.method == 'POST':
        ip = request.remote_addr
        username = request.form.get('username').strip()
        realname = request.form.get('realname').strip()
        if realname == '':
            realname = username
        password = request.form.get('password')
        dept_id = request.form.get('dept')
        type = request.form.get('type')
        permission = ','.join(request.form.getlist('permission'))
        error = None

        if not username:
            error = 'Username is required.'
        if db.execute('SELECT id FROM employee WHERE username = ? and id != ?',
                      (username, id)).fetchone() is not None:
            error = 'Username {0} is already existed.'.format(username)
        if not dept_id:
            error = 'Department is required.'
        if not type:
            error = 'Type is required.'
        if type == '1' and permission == '':
            error = 'At least one permission must be selected for Administrator.'

        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE employee'
                ' SET username = ?, realname = ?, dept_id = ?, type = ?, permission = ?'
                ' WHERE id = ?',
                (username, realname, dept_id, type, permission, id))
            if password != '':
                db.execute('UPDATE employee SET password = ? WHERE id = ?',
                           (generate_password_hash(password), id))
            db.commit()
            current_app.logger.info(
                'UID:%s(%s)-%s update UID:%s{%s,%s,%s}', g.user['id'], g.user['realname'], ip, id, username, realname, dept_id)
            return redirect(url_for('empl.index'))

    return render_template('empl/update.html', empl=empl, permission=permission_list, depts=depts)


@bp.route('/<int:id>/delete', methods=('POST',))
@super_required
def delete(id):
    '''Delete a employee by id.

    Ensures that the employee exists.
    '''
    get_empl(id)
    ip = request.remote_addr
    db = get_db()
    db.execute('DELETE FROM employee WHERE id = ?', (id,))
    db.commit()
    current_app.logger.info('UID:%s(%s)-%s delete UID:%s',
                            g.user['id'], g.user['realname'], ip, id)
    return redirect(url_for('empl.index'))
