from utils.paths import to_abs_path
import re
from cmd.db_helpers import item_exists
from collections import namedtuple

from flask import session
from utils.response import terminal_prefix, InvalidCmdError
from const import PARENT_ID, PARENT_ABS_PATH
from cmd import CD_CMD, validate_args_len

CD_RE = r'^cd ([./a-zA-Z0-9 _-]+)$'  # CD [FOLDER]
CdArgs = namedtuple("CdArgs", ['path', 'folder_id'])

CD_USAGE_DOC = '''
usage: ls [-l] FOLDER
       ls --help
'''


def check_cd_cmd_args(cmd_args, db):
    # called when CMD_ARGS_CHECKER["cd"]() invoked
    validate_args_len(CD_CMD, cmd_args, exact=1)

    _folder = cmd_args[0]

    if _folder == "--help":
        raise InvalidCmdError(
            message=f'User requested usage docs of `cmd`',
            ui_msg=CD_USAGE_DOC)

    if _folder.contains("*"):
        raise InvalidCmdError(
            message=f'cd: FOLDER cannot contain *: {_folder}'
        )

    abs_path = to_abs_path(_folder)

    folder_exists, folder_id = item_exists(
        abs_path=abs_path, check_is_dir=True, db=db)

    if not folder_exists:
        raise InvalidCmdError(
            message=f'cd: no such directory: {_folder}')

    return CdArgs(abs_path, folder_id)


def execute_cd_cmd(cd_args, db):
    print(f'Executing cd cmd')
    session[PARENT_ABS_PATH] = cd_args.path
    session[PARENT_ID] = cd_args.folder_id
    session.modified = True

    print("CD parent_id -> {}".format(cd_args.folder_id))
    print("session[PARENT_ID]=", session[PARENT_ID])
    return {
        "newDir": terminal_prefix(session[PARENT_ABS_PATH]),
    }
