#!/usr/bin/env python3

import os
import sqlite3
from datetime import datetime

import click

import OLMS

app = OLMS.create_app()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        ctx.invoke(run)


@cli.command(short_help='Initialize Database')
def init_db(auth):
    db = sqlite3.connect(app.config['DATABASE'])
    with app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo('Initialized the database.')


@cli.command(short_help='Backup Database')
def backup_db():
    db = sqlite3.connect(app.config['DATABASE'])
    bck = sqlite3.connect(os.path.join(
        app.instance_path, 'backup'+datetime.today().strftime('-%Y%m%d')))
    db.backup(bck)
    db.close()
    bck.close()
    click.echo('Backup done.')


@cli.command(short_help='run OLMS')
@click.option('--port', '-p', default=80, help='Listening Port')
@click.option('--debug', is_flag=True, hidden=True)
def run(port, debug):
    app.run(host='0.0.0.0', port=port, debug=debug)


if __name__ == '__main__':
    cli()
