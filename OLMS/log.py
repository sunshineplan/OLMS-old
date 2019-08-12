import logging
import os
from logging.handlers import RotatingFileHandler


def getLogger(app):
    logger = FileLogger(app)
    return logger


def FileLogger(app):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(os.path.join(
        app.instance_path, 'admin.log'), maxBytes=10*1024*1024, backupCount=100, encoding='utf8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    return logger
