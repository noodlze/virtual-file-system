
from utils.paths import to_abs_path
from collections import namedtuple
from cmd.db_helpers import item_exists, delete_item
from models.ancestors import Ancestors

# rm PATH
RM_RE = r'^rm [\"\']?([*./a-zA-Z0-9 _-]+)[\"\']?$'
RM_CMD = "rm_cmd"
RmArgs = namedtuple("RmArgs", ["path", "item_id"])


def validate_rm_cmd_args(match, db):
  # validator and args extractor
    # returns namedtuple if valid
    path = match.group(1)
    abs_path = to_abs_path(path)
    exists, item_id = item_exists(abs_path, db)
    if not exists(abs_path):
        raise ValueError(f'rm: no such file or directory: {abs_path}')

    return RmArgs(path, item_id)


def execute_rm_cmd(rm_args, db):
    delete_item(rm_args.item_id, db)
    db.session.commit()