from csv import DictWriter
from io import BytesIO, StringIO

from flask import Blueprint, g, request, send_file

from OLMS.auth import admin_required, login_required, super_required
from OLMS.db import get_db

bp = Blueprint('export', __name__, url_prefix='/export')


def exportCSV(query, fieldnames):
    db = get_db()
    try:
        rows = db.execute(query).fetchall()
    except:
        rows = []
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
    action = request.args.get('action')
    if action == 'Export':
        query = ("SELECT date Date, CASE r.type WHEN 1 THEN 'Overtime' WHEN 0 THEN 'Leave' END Type,"
                 ' ABS(duration) Duration, describe Describe, created Created,'
                 " CASE status WHEN 0 THEN 'Unverified' WHEN 1 THEN 'Verified' WHEN 2 THEN 'Rejected' END Status"
                 ' FROM record r JOIN employee e ON r.empl_id = e.id LEFT JOIN department d ON r.dept_id = d.id'
                 ' WHERE r.empl_id = {} {}'
                 ' ORDER BY created DESC')
    elif action == '导出':
        query = ("SELECT date 日期, CASE r.type WHEN 1 THEN '加班' WHEN 0 THEN '休假' END 类型,"
                 ' ABS(duration) 时长, describe 描述, created 创建日期,'
                 " CASE status WHEN 0 THEN '未审核' WHEN 1 THEN '已通过' WHEN 2 THEN '已驳回' END 状态"
                 ' FROM record r JOIN employee e ON r.empl_id = e.id LEFT JOIN department d ON r.dept_id = d.id'
                 ' WHERE r.empl_id = {} {}'
                 ' ORDER BY created DESC')
    else:
        query = '{}{}'
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
    if action == '导出':
        fieldnames = ['日期', '类型', '时长', '描述', '创建日期', '状态']
    else:
        fieldnames = ['Date', 'Type', 'Duration',
                      'Describe', 'Created', 'Status']
    download_file = exportCSV(query.format(
        g.user['id'], condition), fieldnames)
    empl_name = g.user['realname']
    if action == '导出':
        filename = f'员工记录-{empl_name}{year}{month}.csv'.replace('None', '')
    else:
        filename = f'EmplRecords-{empl_name}{year}{month}.csv'.replace(
            'None', '')
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
    action = request.args.get('action')
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    if action == 'Export':
        query = ('SELECT d.dept_name Department, realname Realname, date Date,'
                 " CASE r.type WHEN 1 THEN 'Overtime' WHEN 0 THEN 'Leave' END Type,"
                 ' ABS(duration) Duration, describe Describe, created Created,'
                 " CASE status WHEN 0 THEN 'Unverified' WHEN 1 THEN 'Verified' WHEN 2 THEN 'Rejected' END Status"
                 ' FROM record r JOIN employee e ON empl_id = e.id JOIN department d ON r.dept_id = d.id'
                 ' WHERE {} {}'
                 ' ORDER BY created DESC')
    elif action == '导出':
        query = ('SELECT d.dept_name 部门, realname 姓名, date 日期,'
                 " CASE r.type WHEN 1 THEN '加班' WHEN 0 THEN '休假' END 类型,"
                 ' ABS(duration) 时长, describe 描述, created 创建日期,'
                 " CASE status WHEN 0 THEN '未审核' WHEN 1 THEN '已通过' WHEN 2 THEN '已驳回' END 状态"
                 ' FROM record r JOIN employee e ON empl_id = e.id JOIN department d ON r.dept_id = d.id'
                 ' WHERE {} {}'
                 ' ORDER BY created DESC')
    else:
        query = '{}{}'
    db = get_db()
    if filter:
        if filter == 'dept' and dept_id:
            prefix = '-' + db.execute('SELECT dept_name FROM department'
                                      ' WHERE id = ?', (dept_id,)).fetchone()['dept_name']
            condition1 = 'r.dept_id = {}'.format(dept_id)
        elif filter == 'empl' and empl_id:
            prefix = '-' + db.execute('SELECT realname FROM employee'
                                      ' WHERE id = ?', (empl_id,)).fetchone()['realname']
            condition1 = 'empl_id = {}'.format(empl_id)
    else:
        prefix = ''
        condition1 = 'r.dept_id IN ({})'.format(','.join(permission_list))
    condition2 = ''
    if year:
        if not month:
            condition2 += "AND strftime('%Y', date) = '{}'".format(year)
        else:
            condition2 += "AND strftime('%Y%m', date) = '{}'".format(year+month)
    if type:
        condition2 += ' AND r.type = {}'.format(type)
    if status:
        condition2 += ' AND status = {}'.format(status)
    if action == '导出':
        fieldnames = ['部门', '姓名', '日期', '类型', '时长', '描述', '创建日期', '状态']
    else:
        fieldnames = ['Department', 'Realname', 'Date', 'Type',
                      'Duration', 'Describe', 'Created', 'Status']
    download_file = exportCSV(query.format(condition1, condition2), fieldnames)
    if action == '导出':
        filename = f'部门员工记录{prefix}{year}{month}.csv'.replace('None', '')
    else:
        filename = f'DeptRecords{prefix}{year}{month}.csv'.replace('None', '')
    return send_file(download_file, attachment_filename=filename, as_attachment=True)


@bp.route('/empl/stats')
@login_required
def empl_stats():
    '''Export all the statistics match the filter and belong the current user.'''
    period = request.args.get('period')
    year = request.args.get('year')
    month = request.args.get('month')
    action = request.args.get('action')
    if not period or period == 'month':
        if action == 'Export':
            query = ('SELECT period Period, dept_name Department, realname Realname,'
                     ' overtime Overtime, leave Leave, summary Summary'
                     ' FROM statistics WHERE empl_id = {} {}')
        elif action == '导出':
            query = ('SELECT period 周期, dept_name 部门, realname 姓名,'
                     ' overtime 加班, leave 休假, summary 汇总'
                     ' FROM statistics WHERE empl_id = {} {}')
        else:
            query = '{}{}'
        if not month:
            if not year:
                condition = ''
            else:
                condition = "AND substr(period,1,4) = '{}'".format(year)
        else:
            condition = "AND period = '{}'".format(year+'-'+month)
    elif period == 'year':
        if action == 'Export':
            query = ('SELECT substr(period,1,4) Period, dept_name Department, realname Realname,'
                     ' sum(overtime) Overtime, sum(leave) Leave, sum(summary) Summary'
                     ' FROM statistics WHERE empl_id = {} {}'
                     ' GROUP BY Period, dept_id, empl_id'
                     ' ORDER BY Period DESC')
        elif action == '导出':
            query = ('SELECT substr(period,1,4) 周期, dept_name 部门, realname 姓名,'
                     ' sum(overtime) 加班, sum(leave) 休假, sum(summary) 汇总'
                     ' FROM statistics WHERE empl_id = {} {}'
                     ' GROUP BY 周期, dept_id, empl_id'
                     ' ORDER BY 周期 DESC')
        else:
            query = '{}{}'
        if not year:
            condition = ''
        else:
            condition = "AND year = '{}'".format(year)
    if action == '导出':
        fieldnames = ['周期', '部门', '姓名', '加班', '休假', '汇总']
    else:
        fieldnames = ['Period', 'Department',
                      'Realname', 'Overtime', 'Leave', 'Summary']
    download_file = exportCSV(query.format(
        g.user['id'], condition), fieldnames)
    empl_name = g.user['realname']
    if action == '导出':
        filename = f'员工统计-{empl_name}{year}{month}.csv'.replace('None', '')
    else:
        filename = f'EmplStats-{empl_name}{year}{month}.csv'.replace(
            'None', '')
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
    action = request.args.get('action')
    try:
        permission_list = g.user['permission'].split(',')
    except ValueError:
        permission_list = []
    if not period or period == 'month':
        if action == 'Export':
            query = ('SELECT period Period, dept_name Department, realname Realname,'
                     ' overtime Overtime, leave Leave, summary Summary'
                     ' FROM statistics WHERE 1=1 {}')
        elif action == '导出':
            query = ('SELECT period 周期, dept_name 部门, realname 姓名,'
                     ' overtime 加班, leave 休假, summary 汇总'
                     ' FROM statistics WHERE 1=1 {}')
        else:
            query = '{}'
        if not month:
            if not year:
                condition = ''
            else:
                condition = "AND substr(period,1,4) = '{}'".format(year)
        else:
            condition = "AND period = '{}'".format(year+'-'+month)
    elif period == 'year':
        if action == 'Export':
            query = ('SELECT substr(period,1,4) Period, dept_name Department, realname Realname,'
                     ' sum(overtime) Overtime, sum(leave) Leave, sum(summary) Summary'
                     ' FROM statistics WHERE 1=1 {}'
                     ' GROUP BY Period, dept_id, empl_id'
                     ' ORDER BY Period DESC')
        elif action == '导出':
            query = ('SELECT substr(period,1,4) Period, dept_name Department, realname Realname,'
                     ' sum(overtime) Overtime, sum(leave) Leave, sum(summary) Summary'
                     ' FROM statistics WHERE 1=1 {}'
                     ' GROUP BY Period, dept_id, empl_id'
                     ' ORDER BY Period DESC')
        else:
            query = '{}'
        if not year:
            condition = ''
        else:
            condition = "AND year = '{}'".format(year)
    db = get_db()
    if filter:
        if filter == 'dept' and dept_id:
            prefix = '-' + db.execute('SELECT dept_name FROM department'
                                      ' WHERE id = ?', (dept_id,)).fetchone()['dept_name']
            condition += 'AND dept_id = {}'.format(dept_id)
        elif filter == 'empl' and empl_id:
            prefix = '-' + db.execute('SELECT realname FROM employee'
                                      ' WHERE id = ?', (empl_id,)).fetchone()['realname']
            condition += 'AND empl_id = {}'.format(empl_id)
    else:
        prefix = ''
        condition += 'AND dept_id IN ({})'.format(','.join(permission_list))
    if action == '导出':
        fieldnames = ['周期', '部门', '姓名', '加班', '休假', '汇总']
    else:
        fieldnames = ['Period', 'Department',
                      'Realname', 'Overtime', 'Leave', 'Summary']
    download_file = exportCSV(query.format(condition), fieldnames)
    if action == '导出':
        filename = f'部门员工统计{prefix}{year}{month}.csv'.replace('None', '')
    else:
        filename = f'DeptStats{prefix}{year}{month}.csv'.replace('None', '')
    return send_file(download_file, attachment_filename=filename, as_attachment=True)
