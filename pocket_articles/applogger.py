import logging
from logging.handlers import RotatingFileHandler
import os

LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'pocketlog.log')
_log_format = '%(asctime)s [%(levelname)s] (%(name)s - %(filename)s.%(funcName)s(%(lineno)d)): %(message)s'


def get_file_handler():
    """Return handler"""
    f_handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=1)
    f_handler.setLevel(logging.DEBUG)
    f_handler.setFormatter(logging.Formatter(_log_format))
    return f_handler


def get_stream_handler():
    """Return stream handler"""
    s_handler = logging.StreamHandler()
    s_handler.setLevel(logging.ERROR)
    s_handler.setFormatter(logging.Formatter(_log_format))
    return s_handler


def get_logger(name):
    """Return logging logger

    Args:
        name (str): Имя модуля.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    logger.addHandler(get_file_handler())
    logger.addHandler(get_stream_handler())
    return logger
