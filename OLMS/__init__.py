import os
import sys
from urllib.request import urlopen

from flask import Flask


class localFlask(Flask):
    def process_response(self, response):
        response.headers['Server'] = 'webapp'
        super(localFlask, self).process_response(response)
        return(response)


def create_app(mode=None):
    '''Create and configure an instance of the Flask application.'''
    if not mode:
        app = Flask(__name__, instance_relative_config=True)
        # store the database in the instance folder
        app.config['DATABASE'] = os.path.join(app.instance_path, 'OLMS.db')
    else:
        static_folder = os.path.join(sys._MEIPASS, 'static')
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        instance_path = os.path.join(os.environ['LOCALAPPDATA'], 'webapp')
        app = localFlask('webapp', static_folder=static_folder, template_folder=template_folder,
                         instance_path=instance_path, instance_relative_config=True)
        app.config['DATABASE'] = os.path.join(app.instance_path, 'database')
    # load config from config.py
    from OLMS import config
    app.config.from_object(config)
    # load custom config from instance/config.py
    app.config.from_pyfile('config.py', silent=True)

    # ensure jquery.js and bootstrap.css exists
    static_files = {
        'jquery.js': 'http://code.jquery.com/jquery-3.4.1.min.js',
        'bootstrap.css': 'http://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css',
        'bootstrap.min.css.map': 'http://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css.map'
    }
    for i in static_files.keys():
        static_file_path = os.path.join(app.static_folder, i)
        if not os.path.isfile(static_file_path):
            try:
                static_file = urlopen(static_files[i], timeout=5)
                with open(static_file_path, 'wb') as f:
                    f.write(static_file.read())
            except:
                pass

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Add custom logger
    from OLMS.log import Logger

    app.log = Logger(app)

    # register the database commands
    from OLMS import db

    db.init_app(app)

    # embed google reCAPTCHA protection
    from OLMS.recaptcha import reCAPTCHA

    @app.context_processor
    def embed_recaptcha():
        return dict(recaptcha=reCAPTCHA())

    # apply the blueprints to the app
    from OLMS import auth, dept, empl, export, record, stats

    app.register_blueprint(auth.bp)
    app.register_blueprint(dept.bp)
    app.register_blueprint(empl.bp)
    app.register_blueprint(export.bp)
    app.register_blueprint(record.bp)
    app.register_blueprint(stats.bp)

    # make url_for('index') == url_for('record.empl_index')
    app.add_url_rule('/', endpoint='index')

    return app
