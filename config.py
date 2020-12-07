import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
print("loading .env file")
load_dotenv(os.path.join(basedir, '.env'))
print('expect non-null value ENGINE_URI=', os.environ.get('ENGINE_URI'))


class Config:
    """Base config."""
    APP_NAME = 'virtual-file-system'
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', None)
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'sessions'

    # seems like heroku cannot load env file -> include engine uri here though bad pracice
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'ENGINE_URI', None)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = False

    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
