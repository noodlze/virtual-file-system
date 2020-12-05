from const import BASE_DIR_ID
import os
import re
from utils.response import InvalidCmdError
from utils.paths import to_abs_path
from cmd.db_helpers import item_exists, splitall, add_new_item
from collections import namedtuple
from cmd import CR_CMD, validate_args_len

# CR -p PATH [DATA]
CR_RE = r'^cr( -p)*( [\"\']?[./a-zA-Z0-9 _-]+[\"\']?)( [\"\']?.+[\"\']?)*$'
CrArgs = namedtuple("CrArgs", ["requires_create", "parent_id", "path", "data"])
FILE_NAME_RE = r'^[a-zA-Z0-9 _-]+$'

CR_USAGE_DOC = '''
usage: cr [-p] PATH [DATA]
       cr --help
'''


def valid_item_name(name):
    _name, ext = os.path.splitext(name)
    return True if re.fullmatch(FILE_NAME_RE, _name) else False


def validate_cr_path(path):
    abs_path = to_abs_path(path)

    # validate filename
    basename = os.path.basename(path)  # if file then also contains ext
    valid_name = valid_item_name(basename)

    if not valid_name:
        raise InvalidCmdError(
            message=f'cr: Invalid filename in PATH arg: {path}')

    return abs_path


def check_cr_cmd_args(cmd_args, db):
    # min = 1 args (PATH), max = 3 args (-p PATH [DATA])
    validate_args_len(min_len=1, max_len=3)

    if len(cmd_args) == 1 and cmd_args[0] == "--help":
        raise InvalidCmdError(
            message=f'User requested usage docs of `cr`', ui_msg=CR_USAGE_DOC)

    abs_path = None

    # only one arg
    if len(cmd_args) == 1:  # only specify path
        if cmd_args[0] == '-p':
            raise InvalidCmdError(
                message=f'cr: Missing required PATH arg: {" ".join(cmd_args)}')

        abs_path = validate_cr_path(cmd_args[0])

    # identify allow_create and abs_path variable value
    # first arg either -p / PATH
    allow_create = False
    to_process_indx = 0
    if cmd_args[0] == "-p":
        allow_create = True
        abs_path = validate_cr_path(cmd_args[1])
        to_process_indx = 2
    else:
        abs_path = validate_cr_path(cmd_args[0])
        to_process_index = 1
     # sure to have abs_path and allow_create variables at this point

    # path given to cr cmd cannot contain *
    if abs_path.contains("*"):
        raise InvalidCmdError(
            message=f'cr: PATH cannot contain *: {" ".join(cmd_args)}')

    # check if data arg given
    data = None
    if len(cmd_args) > to_process_index:
        data = cmd_args[to_process_index]

    # check if abs_path exists
    i_exists, _ = item_exists(abs_path=abs_path, db=db)
    print(f'does item {abs_path} exist={i_exists}')
    if i_exists:
        raise InvalidCmdError(message=f'cr: {abs_path}: File exists')

    # if item does not exist, does the parent dir exist?
    parent_exists, parent_id = item_exists(
        abs_path=os.path.dirname(abs_path), db=db)

    if not parent_exists and not allow_create:
        raise InvalidCmdError(
            message=f'cr no such file or directory: {abs_path}')

    requires_create = True if (allow_create and not parent_exists) else False

    return CrArgs(requires_create, parent_id, abs_path, data)


def execute_cr_cmd(cr_args, db):
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
            exists, item_id = item_exists(abs_path=_path_itr, db=db)
            if exists:  # already exists
                parent_id = item_id
            else:  # add new item
                parent_id = add_new_item(
                    name=p, item_parent_id=parent_id, db=db)  # create a directory
    else:
        parent_id = cr_args.parent_id

    # add new item to the parent id
    print("cr_args.data=", cr_args.data)
    add_new_item(name=item_name, item_parent_id=parent_id,
                 db=db, data=cr_args.data)
    resp = {
        "response": "Created {}".format(cr_args.path)
    }

    db.session.commit()

    return resp
