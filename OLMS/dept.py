from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)
from werkzeug.security import generate_password_hash

from OLMS.auth import super_required
from OLMS.db import get_db

bp = Blueprint('dept', __name__, url_prefix='/manage/dept')


@bp.route('')
@super_required
def index():
    '''Show all the departments.'''
    db = get_db()
    depts = db.execute('SELECT * FROM department').fetchall()
    return render_template('dept/index.html', depts=depts)


def get_dept(id):
    '''Get a department by id.

    Checks that the id exists.
    :param id: id of department to get
    :return: the department information
    :raise 404: if a department with the given id doesn't exist
    '''
    dept = get_db().execute('SELECT * FROM department WHERE id = ?',
                            (id,)).fetchone()
    if dept is None:
        abort(404, "Department id {0} doesn't exist.".format(id))
    return dept


@bp.route('/add', methods=('GET', 'POST'))
@super_required
def add():
    '''Add a new department.

    Validates that the department name is not already taken.
    '''
    if request.method == 'POST':
        department = request.form.get('dept').strip()
        db = get_db()
        error = None

        if not department:
            error = 'Department name is required.'
        if db.execute('SELECT id FROM department WHERE dept_name = ?',
                      (department,)).fetchone() is not None:
            error = 'Department {0} is already existed.'.format(department)

        if error is not None:
            flash(error)
        else:
            # the department name is available, store it in the database
            db.execute(
                'INSERT INTO department (dept_name) VALUES (?)', (department,))
            db.execute(
                'UPDATE employee SET permission = (SELECT group_concat(id) FROM department) WHERE id = 0')
            db.commit()
            return redirect(url_for('dept.index'))

    return render_template('dept/add.html')


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@super_required
def update(id):
    '''Update a department by id.

    Ensures that the department exists.
    '''
    dept = get_dept(id)
    if request.method == 'POST':
        department = request.form.get('dept').strip()
        error = None
        db = get_db()

        if not department:
            error = 'Department name is required.'
        if db.execute(
            'SELECT id FROM department WHERE dept_name = ? and id != ?',
                (department, id)).fetchone() is not None:
            error = 'Department {0} is already existed.'.format(department)

        if error is not None:
            flash(error)
        else:
            db.execute('UPDATE department SET dept_name = ? WHERE id = ?',
                       (department, id))
            db.commit()
            return redirect(url_for('dept.index'))

    return render_template('dept/update.html', dept=dept)


@bp.route('/<int:id>/delete', methods=('POST',))
@super_required
def delete(id):
    '''Delete a department by id.

    Ensures that the department exists.
    '''
    get_dept(id)
    db = get_db()
    db.execute('DELETE FROM department WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('dept.index'))
