from const import BASE_DIR_ID
import os
import re
import argparse
from utils.response import InvalidCmdError
from utils.paths import to_abs_path
from utils.db_session import provide_db_session
from cmd.db_helpers import item_exists, splitall, add_new_item, to_abs_path_ids
from collections import namedtuple
import sys

# CR [-p] PATH [DATA]
CrArgs = namedtuple("CrArgs", ["requires_create", "parent_id", "path", "data"])
FILE_NAME_RE = r'^[a-zA-Z0-9 _-]+$'


def validate_item_name(name):
    _name, ext = os.path.splitext(name)
    valid_name = re.fullmatch(FILE_NAME_RE, _name)

    if not valid_name:
        raise InvalidCmdError(
            message=f'cr: Invalid filename in PATH arg: {name}')


@provide_db_session
def check_cr_cmd_args(cmd_args, db=None):
    cr_parser = argparse.ArgumentParser(description="create folders/files")

    cr_parser.add_argument('path', metavar='PATH', nargs=1)
    cr_parser.add_argument('-p', action='store_true')
    cr_parser.add_argument('data', metavar='DATA', nargs='?', default=None)

    try:
        parsed_args = cr_parser.parse_args(cmd_args)

        # extract and validate value of path, allow_create, data args
        allow_create = True if parsed_args.p else False

        path = parsed_args.path[0]
        abs_path = to_abs_path(path)
        # cr path arg cannot contain *
        if '*' in abs_path:
            raise InvalidCmdError(
                message=f'cr: PATH cannot contain *: {" ".join(cmd_args)}')
        validate_item_name(os.path.basename(abs_path))

        data = parsed_args.data

        # check if abs_path exists
        # dest_path_parts, dest_path_parts_id = to_abs_path_ids(abs_path=abs_path)
        i_exists, _ = item_exists(abs_path=abs_path)
        print(f'does item {abs_path} exist={i_exists}')
        if i_exists:
            raise InvalidCmdError(message=f'cr: {abs_path}: File exists')

        # if item does not exist, does the parent dir exist?
        parent_exists, parent_id = item_exists(
            abs_path=os.path.dirname(abs_path))

        # parent dir does not exist + unable to create parent dir
        if not parent_exists and not allow_create:
            raise InvalidCmdError(
                message=f'cr no such file or directory: {abs_path}')

        requires_create = True if (
            allow_create and not parent_exists) else False

        return CrArgs(requires_create, parent_id, abs_path, data)

    except SystemExit as e:
        # (str(e) == "0") -> --help/-h
        err_msg = cr_parser.format_help() \
            if str(e) == "0" else cr_parser.format_usage()

        raise InvalidCmdError(message=err_msg)


@provide_db_session
def execute_cr_cmd(cr_args, db=None):
    print("execute cr cmd", cr_args.path)
    print("PARENT_ID={},path={},data={}".format(
        cr_args.parent_id, cr_args.path, cr_args.data))
    all_parts = splitall(cr_args.path)
    item_name = all_parts[-1]
    print("cr -p allparts={}".format(all_parts))
    # identify parent id of path to create
    parent_id = BASE_DIR_ID
    if cr_args.requires_create:
        # TODO: optimize
        parent_id = BASE_DIR_ID
        _path_itr = ""
        for p in all_parts[:-1]:  # create everything in parent directories
            print("Checking item {}".format(p))
            _path_itr += p
            exists, item_id = item_exists(
                abs_path=_path_itr)
            if exists:  # already exists
                parent_id = item_id
            else:  # add new item
                parent_id = add_new_item(
                    name=p, item_parent_id=parent_id)  # create a directory
    else:
        parent_id = cr_args.parent_id

    # add new item to the parent id
    print("cr_args.data=", cr_args.data)
    add_new_item(name=item_name, item_parent_id=parent_id, data=cr_args.data)
    resp = {
        "response": "Created {}".format(cr_args.path)
    }
    return resp
