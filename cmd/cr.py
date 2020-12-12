from const import BASE_DIR_ID
import os
import re
import argparse
from utils.response import InvalidCmdError
from models.item import Item
from utils.paths import to_abs_path
from utils.db_session import provide_db_session
from cmd.db_helpers import item_exists, splitall, add_new_item, to_abs_path_ids
from collections import namedtuple
import sys

# CR [-p] PATH [DATA]
CrArgs = namedtuple(
    "CrArgs", ["requires_create", "data", "path_parts", "path_parts_id"])
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

        # validate item name
        validate_item_name(os.path.basename(abs_path))

        data = parsed_args.data

        # check if abs_path exists
        path_parts, path_parts_id = to_abs_path_ids(abs_path=abs_path)

        for _item_id in path_parts_id[:-1]:
            # item exists and item is a file
            if _item_id != -1 and not Item.is_a_dir(_item_id):
                raise InvalidCmdError(
                    message=f'cr: {abs_path}: not a directory')

        if path_parts_id[-1] != -1:
            raise InvalidCmdError(message=f'cr: {abs_path}: File exists')

        # if item does not exist, does the parent dir exist?
        parent_exists = True if path_parts_id[-2] != -1 else False

        # parent dir does not exist + unable to create parent dir
        if not parent_exists and not allow_create:
            raise InvalidCmdError(
                message=f'cr no such file or directory: {abs_path}')

        requires_create = True if (
            allow_create and not parent_exists) else False

        return CrArgs(requires_create, data, path_parts, path_parts_id)

    except SystemExit as e:
        # (str(e) == "0") -> --help/-h
        err_msg = cr_parser.format_help() \
            if str(e) == "0" else cr_parser.format_usage()

        raise InvalidCmdError(message=err_msg)


@provide_db_session
def execute_cr_cmd(cr_args, db=None):
    abs_path = '/'.join(cr_args.path_parts)
    print("execute cr cmd", "{}".format(abs_path))
    # identify parent id of path to create
    parent_id = cr_args.path_parts_id[-2]

    if cr_args.requires_create:
        parent_id = cr_args.path_parts_id[0]
        # create second -> last directory
        for _part_name, _part_id in zip(cr_args.path_parts[1:-1], cr_args.path_parts_id[1:-1]):
            if _part_id == -1:  # does not exist
                # create a directory
                created_item_id = add_new_item(
                    name=_part_name, item_parent_id=parent_id)
                # update parent_id
                parent_id = created_item_id
            else:
                parent_id = _part_id

        # add new item to the parent id
    print("cr_args.data=", cr_args.data)
    add_new_item(name=cr_args.path_parts[-1],
                 item_parent_id=parent_id, data=cr_args.data)
    resp = {
        "response": "Created {}".format(abs_path)
    }
    return resp
