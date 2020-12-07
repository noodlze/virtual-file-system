import re
import argparse
from collections import namedtuple
from cmd.db_helpers import list_child_items
from flask import session
from const import PARENT_ID
from utils.response import InvalidCmdError
from utils.db_session import provide_db_session

# LS [-l] [LEVEL]
LsArgs = namedtuple("LsArgs", ["is_verbose", "level"])


@provide_db_session
def check_ls_cmd_args(cmd_args, db=None):
    ls_parser = argparse.ArgumentParser(
        description="list current working directory contents")

    ls_parser.add_argument('-l', action='store_true')
    ls_parser.add_argument(
        'level', type=int, metavar='LEVEL', nargs='?', default=1)

    try:
        parsed_args = ls_parser.parse_args(cmd_args)

        level = int(parsed_args.level)
        is_verbose = True if parsed_args.l else False

        return LsArgs(is_verbose, level)
    except SystemExit as e:
        # (str(e) == "0") -> --help/-h
        err_msg = ls_parser.format_help() \
            if str(e) == "0" else ls_parser.format_usage()

        raise InvalidCmdError(message=err_msg)


def dir_tree_structure(dir_contents, is_verbose=False):
    # hack for server to pretty print file structure
    lines = []
    lines.append(f'Total : {len(dir_contents)}')

    if len(dir_contents) == 0:
        return lines

    # add header
    name_header = "name".ljust(40, ' ')
    header = f'{name_header}'
    if is_verbose:
        created_at_header = "created_at".rjust(30, ' ')
        updated_at_header = "updated_at".rjust(30, ' ')
        size_header = "size".rjust(10, ' ')
        header = f'{created_at_header}{updated_at_header}{size_header}     ' + header
    lines.append(header)

    # add a row for each item in the folder
    for i, (ancestor, item) in enumerate(dir_contents):
        print("ancestor:parent_id={},child_id={},depth={},rank={};id:name={}".format(
            ancestor.parent_id, ancestor.child_id, ancestor.depth, ancestor.rank, item.name))
        level = ancestor.rank.count(',')

        indent = ' ' * 4 * (level)

        # print(f'level={level},indent={indent},item={item.name}')

        details = ''
        if is_verbose:
            created_at = item.created_at.isoformat().rjust(30, ' ')
            updated_at = item.updated_at.isoformat().rjust(30, ' ')
            size = str(item.size).rjust(10, ' ')
            details += f'{created_at}{updated_at}{size}'

        lines.append('{}{}{}{}'.format(details, indent,
                                       item.name,
                                       "/" if item.is_dir else ""))

    return lines


@provide_db_session
def execute_ls_cmd(ls_args, db=None):
    # in  hierarchical order
    print("execute_ls_cmd")
    print("PARENT_ID =", session.get(PARENT_ID, None))
    folder_contents = list_child_items(
        parent_id=session.get(PARENT_ID, 0), depth=ls_args.level)

    resp = {
        "response": dir_tree_structure(folder_contents, ls_args.is_verbose)
    }

    return resp
