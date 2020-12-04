from const import BASE_DIR_ID
import os
from utils.paths import to_abs_path
from cmd.db_helpers import item_exists, splitall, add_new_item
from collections import namedtuple

CR_CMD = "cr_cmd"
# CR -p PATH [DATA]
CR_RE = r'^cr( -p)*( [\"\']?[./a-zA-Z0-9 _-]+[\"\']?)( [\"\']?.+[\"\']?)*$'
CrArgs = namedtuple("CrArgs", ["requires_create", "parent_id", "path", "data"])


def validate_cr_cmd_args(match, db):
    allow_create = True if match.group(1) else False
    path = match.group(2)[1:]
    abs_path = to_abs_path(path)

    i_exists, _ = item_exists(abs_path=abs_path, db=db)
    print(f'does item {abs_path} exist={i_exists}')
    if i_exists:
        raise ValueError(f'cr: {path}: File exists')

    parent_exists, parent_id = item_exists(
        abs_path=os.path.dirname(abs_path), db=db)

    if not parent_exists and not allow_create:
        raise ValueError(f'cr no such file or directory: {abs_path}')

    requires_create = True if (allow_create and not parent_exists) else False

    data = match.group(3)

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
