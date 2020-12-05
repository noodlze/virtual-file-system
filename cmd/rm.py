
from utils.paths import to_abs_path
from collections import namedtuple
from cmd.db_helpers import item_exists, delete_item
from models.ancestors import Ancestors
from flask import session
from const import PARENT_ID

# rm PATH
RM_RE = r'^rm [\"\']?([*./a-zA-Z0-9 _-]+)[\"\']?$'
RmArgs = namedtuple("RmArgs", ["path", "item_id"])


def check_rm_cmd_args(match, db):
    # validator and args extractor
    # returns namedtuple if valid
    path = match.group(1)
    abs_path = to_abs_path(path)
    exists, item_id = item_exists(abs_path=abs_path, db=db)
    if not exists:
        raise ValueError(f'rm: no such file or directory: {abs_path}')

    return RmArgs(path, item_id)


def execute_rm_cmd(rm_args, db):
    print("RM cmd")
    print("PARENT_ID={}, item_id={}".format(
        session[PARENT_ID], rm_args.item_id))
    delete_item(id=rm_args.item_id, db=db)
    db.session.commit()
