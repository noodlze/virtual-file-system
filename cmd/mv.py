import re
import os
from utils.paths import to_abs_path
from cmd.db_helpers import delete_item, item_exists, move_item, with_row_locks
from models.item import Item
from collections import namedtuple


MV_CMD = "mv_cmd"
MvArgs = namedtuple("MvArgs", ["srcs", "srcs_id", "dest"])
# mv SOURCE DESTINATION
# mv SOURCE... DESTINATION
MV_RE = r'^mv((?: [\"\']?[./a-zA-Z0-9 _-]+[\"\']?){1,})( [\"\']?[./a-zA-Z0-9 _-]+[\"\']?)$'


def validate_mv_cmd_args(match, db):
    # TODO: check if dest is a subfolder of srcs!
    dest = match.group(2)
    abs_dest = to_abs_path(dest)

    srcs = []
    srcs_str = match.group(1)
    BRACKETS_RE = r'[\"\'][./a-zA-Z0-9 _-]+[\"\']'
    NO_BRACKETS_RE = r'([./a-zA-Z0-9_-])+'  # no space allowed in a src
    m_brackets = re.findall(BRACKETS_RE, srcs_str)

    if len(m_brackets) == 0:
        srcs = re.findall(NO_BRACKETS_RE, srcs_str)

    if not len(srcs):
        raise ValueError(f'mv missing SOURCE...')

    abs_srcs = [to_abs_path(path) for path in srcs]
    srcs_ids = []
    for s in abs_srcs:
        exists, item_id = item_exists(s, db)

        if not exists:
            raise ValueError(f'mv: no such file or directory: {s}')

        srcs_ids.append(item_id)

    return MvArgs(abs_srcs, srcs_ids, abs_dest)


def execute_mv_cmd(mv_args, db):
    # TODO: deal with wildcards
    if len(mv_args.srcs) == 1:
        # check if parent folder exists
        parent_dest_exists, parent_dest_item_id = item_exists(
            os.path.dirname(mv_args.abs_dest), db)

        if not parent_dest_exists:
            return ValueError(f'mv: no such file or directory: {mv_args.abs_dest}')

        # check if destination item exists
        dest_exists, dest_item_id = item_exists(mv_args.abs_dest, db)
        if dest_exists:
            dest_item_is_dir = with_row_locks(db.session.query(
                Item.is_dir)).filter(Item.id == dest_item_id).first()
            if dest_item_is_dir:
                # a directory
                # move src item to new_parent_id
                move_item(mv_args.srcs_id[0], dest_item_id, db)
            else:  # else dest_item = file
                # delete destination file
                delete_item(dest_item_id, db)
                # insert new file in the same parent directory as the deleted destination file
                move_item(mv_args.src_id[0], parent_dest_item_id, db)
        else:
            # TODO: still uncertain about whether I understood this requirement correctly
            # move the src to the parent_destination folder
            move_item(mv_args.src_id[0], parent_dest_item_id, db)
    else:  # many sources
        dest_exists, dest_item_id = item_exists(mv_args.abs_dest, db)

        if not dest_exists:
            raise ValueError(
                f'mv: no such destination file or directory: {mv_args.abs_dest}')
        dest_item_is_dir = with_row_locks(db.session.query(
            Item.is_dir)).filter(Item.id == dest_item_id).first()

        if not dest_item_is_dir:
            raise ValueError(
                f'mv: no such destination directory: {mv_args.abs_dest}')

        for src_id in mv_args.srcs_id:
            move_item(src_id, dest_item_id,db)

    db.session.commit()
