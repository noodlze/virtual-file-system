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
    SECRET_KEY = os.environ.get('SECRET_KEY', 'vnVl8ycSmt6b6veHk4KP')
    SESSION_TYPE = 'sqlalchemy'
    SESSION_SQLALCHEMY_TABLE = 'sessions'

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'ENGINE_URI', 'postgresql+psycopg2://thuypham:root@localhost:5432/file_system')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = False

    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
