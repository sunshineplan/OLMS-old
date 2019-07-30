#!/usr/bin/env python3

import os
import smtplib
import sqlite3
import subprocess
import sys
from datetime import datetime
from email.message import EmailMessage
from shutil import copy

import click

import OLMS

if getattr(sys, 'frozen', False):
    app = OLMS.create_app(mode='exe')
else:
    app = OLMS.create_app()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command(short_help='Initialize Database')
def init_db():
    db = sqlite3.connect(app.config['DATABASE'])
    try:
        with open(os.path.join(sys._MEIPASS, 'templates', 'schema.sql')) as f:
            db.executescript(f.read())
    except:
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
    click.echo('Initialized the database.')


@cli.command(short_help='Backup Database')
@click.option('--location', '-l', default=app.instance_path, help='Backup file location')
@click.option('--email', '-e', default=None, help='Send backup file as mail attachment to specified account')
def backup_db(location, email):
    db = sqlite3.connect(app.config['DATABASE'])
    bckfn = 'backup' + datetime.today().strftime('%Y%m%d')
    bckf = os.path.join(location, bckfn)
    bck = sqlite3.connect(bckf)
    db.backup(bck)
    db.close()
    bck.close()
    click.echo('Backup done.')
    if email:
        msg = EmailMessage()
        msg['Subject'] = bckfn.upper()
        msg['From'] = 'no-reply@shlib.cf'
        msg['To'] = email
        with open(bckf, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application',
                               subtype='octet-stream', filename=bckfn)
        with smtplib.SMTP('smtp.shlib.cf') as s:
            s.send_message(msg)
        os.remove(bckf)
        click.echo('Email done.')


@cli.command(short_help='Install Service')
def install():
    if os.path.splitext(sys.argv[0])[1] == '.exe':
        binPath = copy(sys.executable, os.environ['windir'])
        subprocess.run(['sc', 'create', 'webapp', 'binPath=', binPath,
                        'start=', 'auto', 'depend=', 'tcpip'], shell=True)
        init_db()
        subprocess.run(['sc', 'start', 'webapp'], shell=True)
        click.echo('Service installed successfully.')
    else:
        click.echo('Error.')


@cli.command(short_help='Uninstall Service')
def uninstall():
    subprocess.run(['sc', 'stop', 'webapp'], shell=True)
    subprocess.run(['sc', 'delete', 'webapp'], shell=True)
    click.echo('Service uninstalled successfully.')


@cli.command(short_help='Run Server')
@click.option('--port', '-p', default=80, help='Listening Port')
@click.option('--debug', is_flag=True, hidden=True)
def run(port, debug):
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    cli()
