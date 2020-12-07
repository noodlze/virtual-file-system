from utils.paths import to_abs_path
from cmd.db_helpers import item_exists
from collections import namedtuple

from flask import session
from utils.db_session import provide_db_session
from utils.response import terminal_prefix, InvalidCmdError
from const import PARENT_ID, PARENT_ABS_PATH
import argparse

CdArgs = namedtuple("CdArgs", ['path', 'folder_id'])


@provide_db_session
def check_cd_cmd_args(cmd_args, db=None):
    # called when CMD_ARGS_CHECKER["cd"]() invoked
    cd_parser = argparse.ArgumentParser(
        description='change the current working directory')

    cd_parser.add_argument('folder', metavar='FOLDER',
                           nargs='?', default=session.get(PARENT_ABS_PATH, "/"))

    try:
        parsed_args = cd_parser.parse_args(cmd_args)

        _folder = parsed_args.folder

        if "*" in _folder:
            raise InvalidCmdError(
                message=f'cd: FOLDER cannot contain *: {_folder}'
            )

        abs_path = to_abs_path(_folder)

        folder_exists, folder_id = item_exists(
            abs_path=abs_path, check_is_dir=True)

        if not folder_exists:
            raise InvalidCmdError(
                message=f'cd: no such directory: {_folder}')

        return CdArgs(abs_path, folder_id)

    except SystemExit as e:
        # (str(e) == "0") -> --help/-h
        err_msg = cd_parser.format_help() \
            if str(e) == "0" else cr_parser.format_usage()

        raise InvalidCmdError(message=err_msg)


@provide_db_session
def execute_cd_cmd(cd_args, db=None):
    print(f'Executing cd cmd')
    session[PARENT_ABS_PATH] = cd_args.path
    session[PARENT_ID] = cd_args.folder_id
    session.modified = True

    print("CD parent_id -> {}".format(cd_args.folder_id))
    print("session[PARENT_ID]=", session[PARENT_ID])
    return {
        "newDir": terminal_prefix(session[PARENT_ABS_PATH]),
    }
