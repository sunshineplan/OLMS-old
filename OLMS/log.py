import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

MONGO = True
try:
    from pymongo import MongoClient
    from pymongo.errors import ServerSelectionTimeoutError
except ImportError:
    MONGO = False


def getLogger(app):
    return Logger(app)


def FileLogger(app):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(os.path.join(
        app.instance_path, 'admin.log'), maxBytes=10*1024*1024, backupCount=100, encoding='utf8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(handler)
    return logger


class Logger:
    def __init__(self, app):
        self.filelogger = FileLogger(app)
        self.mongo_enable = app.config.get('MONGO_ENABLE') or True
        self.mongo_server = app.config.get('MONGO_SERVER') or 'localhost'
        self.mongo_port = app.config.get('MONGO_PORT') or 27017
        self.mongo_database = app.config.get('MONGO_DATABASE') or 'OLMS'
        self.mongo_collection = app.config.get('MONGO_COLLECTION') or 'log'
        self.test()

    def test(self):
        if MONGO and self.mongo_enable:
            try:
                with MongoClient(self.mongo_server, self.mongo_port, serverSelectionTimeoutMS=1000) as client:
                    client.server_info()
            except ServerSelectionTimeoutError:
                self.mongo_enable = False
        else:
            self.mongo_enable = False

    def info(self, msg, data):
        self.filelogger.info(msg, *data.values())
        if self.mongo_enable:
            with MongoClient(self.mongo_server, self.mongo_port) as client:
                c = client[self.mongo_database][self.mongo_collection]
                data['timestamp'] = datetime.utcnow()
                c.insert_one(data).inserted_id
