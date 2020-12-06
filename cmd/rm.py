
from utils.paths import to_abs_path
from collections import namedtuple
from cmd.db_helpers import item_exists, delete_item
from models.ancestors import Ancestors
from flask import session
from const import PARENT_ID
import argparse
from utils.response import InvalidCmdError
from utils.db_session import provide_db_session

# rm PATH
RmArgs = namedtuple("RmArgs", ["path", "item_id"])


@provide_db_session
def check_rm_cmd_args(cmd_args, db=None):
    # called when CMD_ARGS_CHECKER["rm"]() invoked
    rm_parser = argparse.ArgumentParser(
        description='remove file/folder')

    rm_parser.add_argument('path', metavar='PATH', nargs=1)

    try:
        parsed_args = rm_parser.parse_args(cmd_args)

        path = parsed_args.path[0]
        abs_path = to_abs_path(path)
        exists, item_id = item_exists(abs_path=abs_path)
        if not exists:
            raise ValueError(f'rm: no such file or directory: {abs_path}')

        return RmArgs(path, item_id)
    except SystemExit as e:
        # (str(e) == "0") -> --help/-h
        err_msg = rm_parser.format_help() \
            if str(e) == "0" else rm_parser.format_usage()

        raise InvalidCmdError(message=err_msg)


@provide_db_session
def execute_rm_cmd(rm_args, db=None):
    print("RM cmd")
    print("PARENT_ID={}, item_id={}".format(
        session[PARENT_ID], rm_args.item_id))
    delete_item(id=rm_args.item_id)

