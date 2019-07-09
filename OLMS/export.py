from csv import DictWriter
from io import BytesIO, StringIO

from flask import Blueprint, g, request, send_file

from OLMS.auth import admin_required, login_required, super_required
from OLMS.db import get_db

bp = Blueprint('export', __name__, url_prefix='/export')


def exportCSV(query, fieldnames):
    db = get_db()
    rows = db.execute(query).fetchall()
    stringIO = StringIO(newline='')
    csv = DictWriter(stringIO, fieldnames, extrasaction='ignore')
    csv.writeheader()
    csv.writerows(rows)
    bytesIO = BytesIO()
    bytesIO.write(stringIO.getvalue().encode('utf-8-sig'))
    bytesIO.seek(0)
    return bytesIO


@bp.route('/empl')
@login_required
def empl_records():
    '''Export all the records match the filter and belong the current user, most recent first.'''
    year = request.args.get('year')
    month = request.args.get('month')
    type = request.args.get('type')
    status = request.args.get('status')
    query = ("SELECT date Date, CASE r.type WHEN 1 THEN 'Overtime' WHEN 0 THEN 'Leave' END Type,"
             ' ABS(duration) Duration, describe Describe, created Created,'
             " CASE status WHEN 0 THEN 'Unverified' WHEN 1 THEN 'Verified' WHEN 2 THEN 'Rejected' END Status"
             ' FROM record r JOIN employee e ON r.empl_id = e.id LEFT JOIN department d ON r.dept_id = d.id'
             ' WHERE r.empl_id = {} {}'
             ' ORDER BY created DESC')
    condition = ''
    if year and year != 'all':
        if not month or month == 'all':
            condition += " AND strftime('%Y', date) = '{}'".format(year)
        else:
            condition += " AND strftime('%Y%m', date) = '{}'".format(year+month)
    if type and type != 'all':
        condition += ' AND r.type = {}'.format(type)
    if status and status != 'all':
        condition += ' AND status = {}'.format(status)
    fieldnames = ['Date', 'Type', 'Duration', 'Describe', 'Created', 'Status']
    download_file = exportCSV(query.format(
        g.user['id'], condition), fieldnames)
    empl_name = g.user['realname']
    filename = f'EmplRecords{empl_name}{year}{month}.csv'.replace(
        'all', '').replace('None', '')
    return send_file(download_file, attachment_filename=filename, as_attachment=True)


@bp.route('/dept')
@admin_required
def dept_records():
    '''Export all the records match the filter and belong the departments which the Administrator has
    the permission, most recent first.'''
    filter = request.args.get('filter')
    dept_id = request.args.get('dept')
    empl_id = request.args.get('empl')
    year = request.args.get('year')
    month = request.args.get('month')
    type = request.args.get('type')
    status = request.args.get('status')
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    query = ('SELECT d.dept_name Department, realname Realname, date Date,'
             " CASE r.type WHEN 1 THEN 'Overtime' WHEN 0 THEN 'Leave' END Type,"
             ' ABS(duration) Duration, describe Describe, created Created,'
             " CASE status WHEN 0 THEN 'Unverified' WHEN 1 THEN 'Verified' WHEN 2 THEN 'Rejected' END Status"
             ' FROM record r JOIN employee e ON empl_id = e.id JOIN department d ON r.dept_id = d.id'
             ' WHERE {} {}'
             ' ORDER BY created DESC')
    db = get_db()
    if filter and filter != 'all':
        if filter == 'dept' and dept_id and dept_id != 'all':
            prefix = db.execute('SELECT dept_name FROM department'
                                ' WHERE id = ?', (dept_id,)).fetchone()['dept_name']
            condition1 = 'r.dept_id = {}'.format(dept_id)
        elif filter == 'empl' and empl_id and empl_id != 'all':
            prefix = db.execute('SELECT realname FROM employee'
                                ' WHERE id = ?', (empl_id,)).fetchone()['realname']
            condition1 = 'empl_id = {}'.format(empl_id)
    else:
        prefix = ''
        condition1 = 'r.dept_id IN ({})'.format(','.join(permission_list))
    condition2 = ''
    if year and year != 'all':
        if not month or month == 'all':
            condition2 += "AND strftime('%Y', date) = '{}'".format(year)
        else:
            condition2 += "AND strftime('%Y%m', date) = '{}'".format(year+month)
    if type and type != 'all':
        condition2 += ' AND r.type = {}'.format(type)
    if status and status != 'all':
        condition2 += ' AND status = {}'.format(status)
    fieldnames = ['Department', 'Realname', 'Date', 'Type',
                  'Duration', 'Describe', 'Created', 'Status']
    download_file = exportCSV(query.format(condition1, condition2), fieldnames)
    filename = f'DeptRecords{prefix}{year}{month}.csv'.replace(
        'all', '').replace('None', '')
    return send_file(download_file, attachment_filename=filename, as_attachment=True)


@bp.route('/empl/stats')
@login_required
def empl_stats():
    '''Export all the statistics match the filter and belong the current user.'''
    period = request.args.get('period')
    year = request.args.get('year')
    month = request.args.get('month')
    if not period or period == 'month':
        query = ('SELECT period Period, dept_name Department, realname Realname,'
                 ' overtime Overtime, leave Leave, summary Summary'
                 ' FROM statistics WHERE empl_id = {} {}')
        if not month or month == 'all':
            if not year or year == 'all':
                condition = ''
            else:
                condition = "AND substr(period,1,4) = '{}'".format(year)
        else:
            condition = "AND period = '{}'".format(year+'-'+month)
    elif period == 'year':
        query = ('SELECT substr(period,1,4) Period, dept_name Department, realname Realname,'
                 ' sum(overtime) Overtime, sum(leave) Leave, sum(summary) Summary'
                 ' FROM statistics WHERE empl_id = {} {}'
                 ' GROUP BY Period, dept_id, empl_id'
                 ' ORDER BY Period DESC')
        if not year or year == 'all':
            condition = ''
        else:
            condition = "AND year = '{}'".format(year)
    fieldnames = ['Period', 'Department', 'Realname', 'Overtime', 'Leave', 'Summary']
    download_file = exportCSV(query.format(
        g.user['id'], condition), fieldnames)
    empl_name = g.user['realname']
    filename = f'EmplStats{empl_name}{year}{month}.csv'.replace(
        'all', '').replace('None', '')
    return send_file(download_file, attachment_filename=filename, as_attachment=True)


@bp.route('/dept/stats')
@admin_required
def dept_stats():
    '''Export all the statistics match the filter and belong the departments which the Administrator has the permission.'''
    filter = request.args.get('filter')
    dept_id = request.args.get('dept')
    empl_id = request.args.get('empl')
    period = request.args.get('period')
    year = request.args.get('year')
    month = request.args.get('month')
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    if not period or period == 'month':
        query = ('SELECT period Period, dept_name Department, realname Realname,'
                 ' overtime Overtime, leave Leave, summary Summary'
                 ' FROM statistics WHERE 1=1 {}')
        if not month or month == 'all':
            if not year or year == 'all':
                condition = ''
            else:
                condition = "AND substr(period,1,4) = '{}'".format(year)
        else:
            condition = "AND period = '{}'".format(year+'-'+month)
    elif period == 'year':
        query = ('SELECT substr(period,1,4) Period, dept_name Department, realname Realname,'
                 ' sum(overtime) Overtime, sum(leave) Leave, sum(summary) Summary'
                 ' FROM statistics WHERE 1=1 {}'
                 ' GROUP BY Period, dept_id, empl_id'
                 ' ORDER BY Period DESC')
        fieldnames = []
        if not year or year == 'all':
            condition = ''
        else:
            condition = "AND year = '{}'".format(year)
    db = get_db()
    if filter and filter != 'all':
        if filter == 'dept' and dept_id and dept_id != 'all':
            prefix = db.execute('SELECT dept_name FROM department'
                                ' WHERE id = ?', (dept_id,)).fetchone()['dept_name']
            condition += 'AND dept_id = {}'.format(dept_id)
        elif filter == 'empl' and empl_id and empl_id != 'all':
            prefix = db.execute('SELECT realname FROM employee'
                                ' WHERE id = ?', (empl_id,)).fetchone()['realname']
            condition += 'AND empl_id = {}'.format(empl_id)
    else:
        prefix = ''
        condition += 'AND dept_id IN ({})'.format(','.join(permission_list))
    fieldnames = ['Period', 'Department', 'Realname', 'Overtime', 'Leave', 'Summary']
    download_file = exportCSV(query.format(condition), fieldnames)
    filename = f'DeptStats{prefix}{year}{month}.csv'.replace(
        'all', '').replace('None', '')
    return send_file(download_file, attachment_filename=filename, as_attachment=True)
