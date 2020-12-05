from cmd import VALID_COMMANDS, CMD_PARSER, CMD_EXECUTOR, CMD_ARGS_CHECKER
from const import BASE_DIR_ID, PARENT_ID, PARENT_ABS_PATH
from utils.response import format_response
from flask import request, session, render_template
from flask_session.__init__ import Session
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from utils.response import terminal_prefix
import shlex
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


def get_cmd(cmd_args):

    if len(cmd_args) == 0:
        raise ValueError(f'{" ".join(cmd_args)}: No command')

    cmd = (cmd_args[0]).lower()
    if cmd in VALID_COMMANDS:
        return cmd

    return None


@app.route("/execute", methods=["POST"])
@format_response
def execute_cmd():
    try:
        user_input = request.json.get(USER_INPUT)
        print(f'Received console input={user_input}')

        # parses cmd line string like `cd "1/2/3"` -> ['cd', '1/2/3']
        # strips parenthesis from each arg
        # returns a list of args
        cmd_args = shlex.split(user_input)

        # check first arg to see if valid cmd
        cmd = get_cmd(cmd_args)

        if not cmd:
            raise ValueError(f'{cmd_args[0]}: command not found')

        # check if cmd args are valid and sufficient
        # only pass args
        # will raise an err if args are valid
        cmd_args_tuple = CMD_ARGS_CHECKER[cmd](cmd_args[1:])

        # helper cmds

        validator_parser_func = CMD_PARSER[input_cmd_type]

        cmd_namedtuple = validator_parser_func(match, db)

        cmd_excutor_func = CMD_EXECUTOR[input_cmd_type]

        return cmd_excutor_func(cmd_namedtuple, db)
    except Exception as e:
        db.session.rollback()
        raise e  # for dev purposes
        # TODO: enable when deploy
        # raise RuntimeError(  # for production
        #     f'{user_input}: something went wrong during cmd execution')


@app.route("/")
def terminal_ui():
    if not session.get(PARENT_ABS_PATH, None):
        session[PARENT_ABS_PATH] = "/"
        session[PARENT_ID] = BASE_DIR_ID

    print(session[PARENT_ABS_PATH], session[PARENT_ID])

    return render_template("base.html", cur_dir=terminal_prefix(session[PARENT_ABS_PATH]))


if __name__ == '__main__':
    app.run()
