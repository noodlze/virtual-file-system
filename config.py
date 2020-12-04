import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base config."""
    APP_NAME = os.environ.get('APP_NAME', 'content-prep')
    TESTING = bool(os.environ.get('TESTING', False))
    SECRET_KEY = os.environ.get('SECRET_KEY')

    SQLALCHEMY_DATABASE_URI = os.environ.get('ENGINE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get(
        'SQLALCHEMY_TRACK_MODIFICATIONS', False)

    SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME', 'session')
    SESSION_COOKIE_SECURE = bool(
        os.environ.get('SESSION_COOKIE_SECURE', False))
    SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', True)
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
