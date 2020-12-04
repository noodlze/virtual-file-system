from blueprints import BASE_DIR_ID
import os
from utils.paths import to_abs_path
from models.utils import item_exists, splitall, add_new_item
from collections import namedtuple
from models import db

CR_CMD = "cr_cmd"
# CR -p PATH [DATA]
CR_RE = r'^cr( -p)*( [\"\']?[./a-zA-Z0-9 _-]+[\"\']?)( [\"\']?.+[\"\']?)*$'
CrArgs = namedtuple("CrArgs", ["requires_create", "parent_id", "path", "data"])


def validate_cr_cmd_args(match):
    allow_create = True if match.group(1) else False
    path = match.group(2)[1:]
    abs_path = to_abs_path(path)

    i_exists, _ = item_exists(abs_path)
    print(f'does item {abs_path} exist={i_exists}')
    if i_exists:
        raise ValueError(f'cr: {path}: File exists')

    parent_exists, parent_id = item_exists(os.path.dirname(abs_path))

    if not parent_exists and not allow_create:
        raise ValueError(f'cr no such file or directory: {abs_path}')

    requires_create = True if (allow_create and not parent_exists) else False

    data = match.group(3)

    return CrArgs(requires_create, parent_id, abs_path, data)


def execute_cr_cmd(cr_args):
    print("execute cr cmd", cr_args.path)
    all_parts = splitall(cr_args.path)
    item_name = all_parts[-1]

    # identify parent id of path to create
    parent_id = None
    if cr_args.requires_create:
        # TODO: optimize
        parent_id = BASE_DIR_ID
        _path_itr = ""
        for p in all_parts[-1]:  # create everything in parent directories
            print("Checking item {}".format(p))
            _path_itr += p
            exists, item_id = item_exists(_path_itr)
            if exists:  # already exists
                parent_id = item_id
            else:  # add new item
                parent_id = add_new_item(p, parent_id)  # create a directory
    else:
        parent_id = cr_args.parent_id

    # add new item to the parent id
    print("cr_args.data=", cr_args.data)
    add_new_item(item_name, parent_id, cr_args.data)
    resp = {
        "response": "Created {}".format(cr_args.path)
    }

    db.session.commit()

    return resp
