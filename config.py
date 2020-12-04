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
        'ENGINE_URI', 'postgres://qfaqxzdlxtirlz:0397be39cfcaf0bbd34053427baf3b64ab1d08c56fc3dab5c7835bf59514b10a@ec2-3-231-48-230.compute-1.amazonaws.com:5432/dbke29vrr6jfru?sslmode=require')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_NAME = 'session'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = False

    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
