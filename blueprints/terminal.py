
from models import db
import re

from flask import request, Blueprint, session, render_template
from utils.response import format_response

from blueprints import BASE_DIR_ID, PARENT_ID, PARENT_ABS_PATH

from blueprints.cmd import terminal_prefix

from blueprints.cmd.cd import CD_RE, CD_CMD, validate_cd_cmd_args, execute_cd_cmd
from blueprints.cmd.ls import LS_RE, LS_CMD, validate_ls_cmd_args, execute_ls_cmd
from blueprints.cmd.cr import CR_RE, CR_CMD, validate_cr_cmd_args, execute_cr_cmd
from blueprints.cmd.mv import MV_RE, MV_CMD, validate_mv_cmd_args, execute_mv_cmd
from blueprints.cmd.rm import RM_RE, RM_CMD, validate_rm_cmd_args, execute_rm_cmd

terminal = Blueprint('terminal', __name__)

USER_INPUT = "user_input"

FILE_NAME_RE = r'^[a-zA-Z0-9 _-]+$'

CMD_TYPE_MAP = [(CD_RE, CD_CMD),
                (LS_RE, LS_CMD),
                (CR_RE, CR_CMD),
                (MV_RE, MV_CMD),
                (RM_RE, RM_CMD)]

CMD_PARSER = {
    CD_CMD: validate_cd_cmd_args,
    LS_CMD: validate_ls_cmd_args,
    CR_CMD: validate_cr_cmd_args,
    MV_CMD: validate_mv_cmd_args,
    RM_CMD: validate_rm_cmd_args,
}

CMD_EXECUTOR = {
    CD_CMD: execute_cd_cmd,
    LS_CMD: execute_ls_cmd,
    CR_CMD: execute_cr_cmd,
    MV_CMD: execute_mv_cmd,
    RM_CMD: execute_rm_cmd,
}


def cmd_type(user_input):
    for cmd_re, _type in CMD_TYPE_MAP:
        m = re.fullmatch(cmd_re, user_input)
        if m:
            return m, _type

    return None, None


@terminal.route("/execute", methods=["POST"])
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

        cmd_namedtuple = validator_parser_func(match)

        cmd_excutor_func = CMD_EXECUTOR[input_cmd_type]

        return cmd_excutor_func(cmd_namedtuple)
    except Exception as e:
        db.session.rollback()
        raise e


@ terminal.route("/")
def terminal_ui():
    if not session.get(PARENT_ABS_PATH, None):
        session[PARENT_ABS_PATH] = "/"
        session[PARENT_ID] = BASE_DIR_ID

    print(session[PARENT_ABS_PATH], session[PARENT_ID])
    return render_template("base.html", cur_dir=terminal_prefix(session[PARENT_ABS_PATH]))
