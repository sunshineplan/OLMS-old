import os
import sqlite3
from datetime import datetime

import click

import OLMS

app = OLMS.create_app()


@click.group()
def cli():
    pass


@cli.command(short_help='Initialize Database')
@click.option('--auth', prompt='Password', help='For Authentication')
def init_db(auth):
    if auth == 'aaa':
        db = sqlite3.connect(app.config['DATABASE'])
        with app.open_resource('schema.sql') as f:
            db.executescript(f.read().decode('utf8'))
        click.echo('Initialized the database.')
    else:
        click.echo('Authentication failed. Bye!')


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
def run(port):
    app.run(port=port)


if __name__ == '__main__':
    cli()
