from flask import Flask
from blueprints.terminal import terminal
from flask_migrate import Migrate, upgrade
from models import db
import os


def create_app():
    flask_app = Flask(__name__)
    print("flask_app")
    # flask app configs
    flask_app.config.from_object('config.Config')
    print("flask_app.config")
    # init db
    migrate = Migrate()
    db.init_app(flask_app)
    print("db.init_app(flask_app)")
    migrate.init_app(flask_app, db, "migrations")
    print("migrate.init_app(flask_app, db, migration)")
    # register blueprints
    flask_app.register_blueprint(terminal)

    return flask_app


app = create_app()

# with app.app_context():
#     upgrade(directory="migrations")  # run db upgrade

if __name__ == "__main__":
    app.run(debug=True)
