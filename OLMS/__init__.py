import os
from datetime import timedelta

from flask import Flask


def create_app():
    '''Create and configure an instance of the Flask application.'''
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY='dev',
        # default expiration date of a permanent session
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=5),
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, 'OLMS.db'),
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # register the database commands
    from OLMS import db

    db.init_app(app)

    # apply the blueprints to the app
    from OLMS import auth, dept, empl, export, record, stats

    app.register_blueprint(auth.bp)
    app.register_blueprint(dept.bp)
    app.register_blueprint(empl.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(record.bp)
    app.register_blueprint(stats.bp)

    # make url_for('index') == url_for('record.empl_index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the record blueprint a url_prefix, but for
    # the tutorial the record will be the main index
    app.add_url_rule('/', endpoint='index')

    return app
