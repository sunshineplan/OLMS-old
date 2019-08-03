from flask import (Blueprint, abort, g, redirect, render_template, request,
                   url_for)

from OLMS.auth import admin_required, login_required
from OLMS.db import get_db
from OLMS.pagination import Pagination

bp = Blueprint('stats', __name__, url_prefix='/stats')


@bp.route('')
@login_required
def empl_index():
    '''Show all the statistics match the filter and belong the current user.'''
    if not g.user['id']:
        return redirect(url_for('stats.dept_index'))
    db = get_db()
    period = request.args.get('period')
    year = request.args.get('year')
    month = request.args.get('month')
    page = request.args.get('page') or 1
    per_page = request.args.get('per_page') or 10
    args = dict(period=period, year=year, month=month,
                page=page, per_page=per_page)
    years = db.execute('SELECT DISTINCT substr(period,1,4) year FROM statistics'
                       ' WHERE empl_id = ? ORDER BY year DESC', (g.user['id'],)).fetchall()
    if not period or period == 'month':
        query = 'SELECT * FROM statistics WHERE empl_id = ? {}'
        if not month:
            if not year:
                condition = ''
            else:
                condition = "AND substr(period,1,4) = '{}'".format(year)
        else:
            condition = "AND period = '{}'".format(year+'-'+month)
    elif period == 'year':
        query = ('SELECT substr(period,1,4) year, dept_name, realname, sum(overtime) overtime, sum(leave) leave, sum(summary) summary'
                 ' FROM statistics WHERE empl_id = ? {}'
                 ' GROUP BY year, dept_id, empl_id'
                 ' ORDER BY year DESC')
        if not year:
            condition = ''
        else:
            condition = "AND year = '{}'".format(year)
    record = len(db.execute(query.format(
        condition), (g.user['id'],)).fetchall())
    limit = ' LIMIT {}, {}'.format((int(page)-1)*int(per_page), int(per_page))
    records = db.execute(query.format(condition)+limit,
                         (g.user['id'],)).fetchall()
    pagination = Pagination(per_page=int(per_page),
                            page=int(page), record=record)
    return render_template('stats/index.html', records=records, years=years, args=args, pagination=pagination, mode='empl')


@bp.route('/dept')
@admin_required
def dept_index():
    '''Show all the statistics match the filter and belong the departments which the Administrator has the permission.'''
    db = get_db()
    dept_id = request.args.get('dept')
    empl_id = request.args.get('empl') or ''
    period = request.args.get('period')
    year = request.args.get('year')
    month = request.args.get('month')
    page = request.args.get('page') or 1
    per_page = request.args.get('per_page') or 10
    args = dict(dept_id=dept_id, empl_id=empl_id, period=period,
                year=year, month=month, page=page, per_page=per_page)
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    depts = db.execute('SELECT * FROM department'
                       ' WHERE id IN ({}) ORDER BY dept_name'.format(','.join(permission_list))).fetchall()
    years = db.execute('SELECT DISTINCT substr(period,1,4) year FROM statistics'
                       ' WHERE dept_id IN ({}) ORDER BY year DESC'.format(','.join(permission_list))).fetchall()
    if not period or period == 'month':
        query = 'SELECT * FROM statistics WHERE 1=1 {}'
        if not month:
            if not year:
                condition = ''
            else:
                condition = "AND substr(period,1,4) = '{}'".format(year)
        else:
            condition = "AND period = '{}'".format(year+'-'+month)
    elif period == 'year':
        query = ('SELECT substr(period,1,4) year, dept_name, realname, sum(overtime) overtime, sum(leave) leave, sum(summary) summary'
                 ' FROM statistics WHERE 1=1 {}'
                 ' GROUP BY year, dept_id, empl_id'
                 ' ORDER BY year DESC')
        if not year:
            condition = ''
        else:
            condition = "AND year = '{}'".format(year)
    if dept_id and not empl_id:
        if dept_id not in permission_list:
            abort(403)
        condition += 'AND dept_id = {}'.format(dept_id)
    elif empl_id:
        if str(db.execute('SELECT * FROM employee WHERE id = ?', (empl_id,)).fetchone()['dept_id']) != dept_id:
            abort(403)
        condition += 'AND empl_id = {}'.format(empl_id)
    else:
        condition += 'AND dept_id IN ({})'.format(','.join(permission_list))
    record = len(db.execute(query.format(condition)).fetchall())
    limit = ' LIMIT {}, {}'.format((int(page)-1)*int(per_page), int(per_page))
    records = db.execute(query.format(condition)+limit).fetchall()
    pagination = Pagination(per_page=int(per_page),
                            page=int(page), record=record)
    return render_template('stats/index.html', records=records, depts=depts, years=years, args=args, pagination=pagination, mode='dept')
