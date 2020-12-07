
from utils.paths import to_abs_path
from collections import namedtuple
from cmd.db_helpers import item_exists, delete_item, item_exists_in_folder, to_abs_path_ids, resolve_asterisk_in_abs_path
from models.ancestors import Ancestors
from flask import session
from const import PARENT_ID
import argparse
from utils.response import InvalidCmdError
from utils.db_session import provide_db_session

# rm PATH
RmArgs = namedtuple("RmArgs", ["path_list", "item_id_list"])


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
        # resolve asterisks
        abs_path_parts_list = resolve_asterisk_in_abs_path(abs_path)

        abs_path_list = ["/".join(parts[0])
                         for parts in abs_path_parts_list]

        for abs_path_parts, abs_path_parts_id in abs_path_parts_list:
            if -1 in abs_path_parts_id:  # some item in the path doesn't exist
                _path = "\n".join(abs_path_list)
                raise ValueError(f'rm: no such file or directory:\n {_path}')

        return RmArgs(path_list=abs_path_list,
                      item_id_list=[parts_id[-1] for parts_id in abs_path_parts_list])
    except SystemExit as e:
        # (str(e) == "0") -> --help/-h
        err_msg = rm_parser.format_help() \
            if str(e) == "0" else rm_parser.format_usage()

        raise InvalidCmdError(message=err_msg)


@ provide_db_session
def execute_rm_cmd(rm_args, db=None):
    removed = []

    for abs_path, item_parts_id in zip(rm_args.path_list, rm_args.item_id_list):
        delete_item(id=item_parts_id[-1])
        removed.append(abs_path)

    resp = {
        "response": 'Removed:\n{}'.format("\n".join(removed))
    }
    return resp
