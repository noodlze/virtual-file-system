from utils.paths import to_abs_path
import re
from cmd.db_helpers import item_exists
from collections import namedtuple

from flask import session
from utils.response import terminal_prefix
from const import PARENT_ID, PARENT_ABS_PATH

CD_CMD = "cd_cmd"
CD_RE = r'^cd ([./a-zA-Z0-9 _-]+)$'  # CD [FOLDER]
CdArgs = namedtuple("CdArgs", ['folder', 'folder_id'])


def validate_cd_cmd_args(match, db):
    _folder = match.group(1)
    abs_path = to_abs_path(_folder)
    exists, item_id = item_exists(abs_path, db)
    print(f'validate cd cmd args {exists}')
    if not exists:
        raise ValueError(f'cd: no such file or directory: {_folder}')

    return CdArgs(abs_path, item_id)


def execute_cd_cmd(cd_args, db):
    print(f'Executing cd cmd')
    session[PARENT_ABS_PATH] = cd_args.folder
    session[PARENT_ID] = cd_args.folder_id
    session.modified = True

    print("CD parent_id -> {}".format(cd_args.folder_id))
    print(cd_args.folder_id)
    return {
        "newDir": terminal_prefix(session[PARENT_ABS_PATH]),
    }
