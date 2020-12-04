from cmd import CMD_TYPE_MAP, CMD_PARSER, CMD_EXECUTOR
from const import BASE_DIR_ID, PARENT_ID, PARENT_ABS_PATH
from utils.response import format_response
from flask import request, session, render_template
from flask_session.__init__ import Session
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from utils.response import terminal_prefix

import re

USER_INPUT = "user_input"

app = Flask(__name__)
app.config.from_object('config.Config')  # flask app configs

_session = Session(app)
_session.app.session_interface.db.create_all()

# with app.app_context():
#     upgrade(directory="migrations")  # run db upgrade

db = SQLAlchemy(app)

# register routes


def cmd_type(user_input):
    for cmd_re, _type in CMD_TYPE_MAP:
        m = re.fullmatch(cmd_re, user_input)
        if m:
            return m, _type

    return None, None


@app.route("/execute", methods=["POST"])
@format_response
def execute_cmd():
    try:
        user_input = request.json.get(USER_INPUT)

        print(f'Received console input={user_input}')
        # helper cmds

        match, input_cmd_type = cmd_type(user_input)
        if not match:
            raise ValueError(f'command not found: {user_input}')

        validator_parser_func = CMD_PARSER[input_cmd_type]

        cmd_namedtuple = validator_parser_func(match, db)

        cmd_excutor_func = CMD_EXECUTOR[input_cmd_type]

        return cmd_excutor_func(cmd_namedtuple, db)
    except Exception as e:
        db.session.rollback()
        raise e


@app.route("/")
def terminal_ui():
    if not session.get(PARENT_ABS_PATH, None):
        session[PARENT_ABS_PATH] = "/"
        session[PARENT_ID] = BASE_DIR_ID

    print(session[PARENT_ABS_PATH], session[PARENT_ID])
    return render_template("base.html", cur_dir=terminal_prefix(session[PARENT_ABS_PATH]))


if __name__ == '__main__':
    app.run()
