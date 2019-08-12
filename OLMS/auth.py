import functools
from time import localtime, strftime, time

from flask import (Blueprint, abort, current_app, flash, g, make_response,
                   redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from OLMS.db import get_db, init_db
from OLMS.recaptcha import reCAPTCHA

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    '''View decorator that redirects anonymous users to the login page.'''

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    '''View decorator that raise 403 if the current user isn't Administrator.'''

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user['type'] == 0:
            return abort(403)
        return view(**kwargs)

    return wrapped_view


def super_required(view):
    '''View decorator that raise 403 if the current user isn't Super Administrator.'''

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        elif g.user['id'] != 0:
            return abort(403)
        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    '''If a user id is stored in the session, load the user object from
    the database into ``g.user``.'''
    user_id = session.get('user_id')
    last = request.cookies.get('Last')
    ip = request.remote_addr
    db = get_db()
    if user_id is None:
        g.user = None
    else:
        if session.get('_permanent') or not last or time()-float(last) < current_app.config.get('SESSION_COOKIE_LIFETIME'):
            g.user = db.execute('SELECT * FROM employee WHERE id = ?',
                                (user_id,)).fetchone()
        else:
            session.clear()
            flash('Session timeout. Please re-login!')
            current_app.log.info('UID:%s-%s time out at %s', user_id,
                                    ip, strftime('%Y-%m-%d %H:%M:%S', localtime(float(last))))
            return redirect(url_for('auth.login'))


@bp.route('/login', methods=('GET', 'POST'))
def login():
    '''Log in a user by adding the user id to the session.'''
    last_visit = request.cookies.get('LastVisit')
    if g.user:
        if last_visit:
            return redirect(last_visit)
        return redirect(url_for('index'))

    if request.method == 'POST':
        ip = request.remote_addr
        username = request.form.get('username')
        password = request.form.get('password')
        rememberme = request.form.get('rememberme')
        db = get_db()
        error = None
        try:
            user = db.execute('SELECT * FROM employee WHERE username = ?',
                              (username,)).fetchone()
        except:
            tables = db.execute('SELECT name FROM sqlite_master').fetchall()
            if tables == []:
                init_db()
                flash('Detected first time running. Initialized the database.')
            else:
                flash('Critical Error! Please contact your system administrator.')
            return render_template('auth/login.html')

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password) and user['password'] != password:
            error = 'Incorrect password.'
            current_app.log.info(
                'UID:%s(%s)-%s password failed', user['id'], user['realname'], ip)
        score = reCAPTCHA().verify
        if not score or score < reCAPTCHA().level:
            error = reCAPTCHA().failed

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session['user_id'] = user['id']
            if rememberme == 'on':
                session.permanent = True
            else:
                session.permanent = False
            current_app.log.info('UID:%s(%s)-%s log in(score:%s)',
                                    user['id'], user['realname'], ip, score)
            if last_visit:
                return redirect(last_visit)
            if user['id']:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('record.dept_index'))

        flash(error)

    response = make_response(render_template('auth/login.html'))
    response.delete_cookie('Last')
    return response


@bp.route('/setting', methods=('GET', 'POST'))
@login_required
def setting():
    '''Change current user's password.'''
    if request.method == 'POST':
        ip = request.remote_addr
        password = request.form.get('password')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        db = get_db()
        error = None
        user = db.execute('SELECT password FROM employee WHERE id = ?',
                          (g.user['id'],)).fetchone()

        if not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        elif password1 != password2:
            error = "Confirm password doesn't match new password."
        elif password1 == password:
            error = 'New password cannot be the same as your current password.'
        elif password1 is None or password1 == '':
            error = 'New password cannot be blank.'
        score = reCAPTCHA().verify
        if not score or score < reCAPTCHA().level:
            error = reCAPTCHA().failed

        if error is None:
            # Store new password in the database and go to
            # the login page
            db.execute(
                'UPDATE employee SET password = ? WHERE id = ?',
                (generate_password_hash(password1), g.user['id']),
            )
            db.commit()
            current_app.log.info('UID:%s(%s)-%s change password(score:%s)',
                                    g.user['id'], g.user['realname'], ip, score)
            session.clear()
            flash('Password Changed. Please Re-login!')
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/setting.html')


@bp.route('/logout')
@login_required
def logout():
    '''Clear the current session, including the stored user id.'''
    ip = request.remote_addr
    current_app.log.info('UID:%s(%s)-%s log out',
                            g.user['id'], g.user['realname'], ip)
    session.clear()
    return redirect(url_for('auth.login'))
