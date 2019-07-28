import logging
import os
import sys
from datetime import timedelta
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask.logging import default_handler


class localFlask(Flask):
    def process_response(self, response):
        response.headers['Server'] = 'webapp'
        super(localFlask, self).process_response(response)
        return(response)


def create_app(mode=None):
    '''Create and configure an instance of the Flask application.'''
    if not mode:
        app = Flask(__name__, instance_relative_config=True)
        app.config.from_mapping(
            # a default secret that should be overridden by instance config
            SECRET_KEY='dev',
            # store the database in the instance folder
            DATABASE=os.path.join(app.instance_path, 'OLMS.db'),
            # default expiration date of a permanent session
            PERMANENT_SESSION_LIFETIME=timedelta(days=365*100),
            # prevent sending the cookie every time
            SESSION_REFRESH_EACH_REQUEST=False,
        )
    else:
        static_folder = os.path.join(sys._MEIPASS, 'static')
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        instance_path = os.path.join(os.environ['LOCALAPPDATA'], 'webapp')
        app = localFlask('webapp', static_folder=static_folder,
                         template_folder=template_folder, instance_path=instance_path)
        app.config.from_mapping(
            # a default secret that should be overridden by instance config
            SECRET_KEY='webapp',
            # store the database in the instance folder
            DATABASE=os.path.join(app.instance_path, 'database'),
            # default expiration date of a permanent session
            PERMANENT_SESSION_LIFETIME=timedelta(days=365*100),
            # prevent sending the cookie every time
            SESSION_REFRESH_EACH_REQUEST=False,
        )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Add custom logger
    app.logger.removeHandler(default_handler)
    app.logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(os.path.join(
        app.instance_path, 'admin.log'), maxBytes=10*1024*1024, backupCount=100)
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    app.logger.addHandler(handler)

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
