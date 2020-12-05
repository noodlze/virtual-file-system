import re
import os
from utils.paths import to_abs_path
from cmd.db_helpers import delete_item, item_exists, move_item, with_row_locks
from models.item import Item
from collections import namedtuple


MvArgs = namedtuple("MvArgs", ["srcs", "srcs_id", "dest"])
# mv SOURCE DESTINATION
# mv SOURCE... DESTINATION
MV_RE = r'^mv((?: [\"\']?[./a-zA-Z0-9 _-]+[\"\']?){1,})( [\"\']?[./a-zA-Z0-9 _-]+[\"\']?)$'


def check_mv_cmd_args(match, db):
    # TODO: check if dest is a subfolder of srcs!
    dest = match.group(2)
    # remove leading space as it messes things up
    abs_dest = to_abs_path(dest[1:])
    print("dest={}".format(abs_dest))
    srcs = []
    srcs_str = match.group(1)[1:]
    print("srcs_str={}".format(srcs_str))
    BRACKETS_RE = r'[\"\'][./a-zA-Z0-9 _-]+[\"\']'
    NO_BRACKETS_RE = r'([./a-zA-Z0-9_-]+)'  # no space allowed in a src
    m_brackets = re.findall(BRACKETS_RE, srcs_str)

    if len(m_brackets) == 0:
        srcs = re.findall(NO_BRACKETS_RE, srcs_str)

    print("srcs={}".format(srcs))

    if not len(srcs):
        raise ValueError(f'mv missing SOURCE...')

    abs_srcs = [to_abs_path(path) for path in srcs]
    srcs_ids = []
    for s in abs_srcs:
        exists, item_id = item_exists(abs_path=s, db=db)

        if not exists:
            raise ValueError(f'mv: no such file or directory: {s}')

        srcs_ids.append(item_id)

    return MvArgs(abs_srcs, srcs_ids, abs_dest)


def execute_mv_cmd(mv_args, db):
    print("executing mv_cmd: srcs={},srcs_id={},dest={}".format(
        mv_args.srcs, mv_args.srcs_id, mv_args.dest))
    # TODO: deal with wildcards
    if len(mv_args.srcs) == 1:
        print("only 1 src")
        # check if parent folder exists
        parent_dest_exists, parent_dest_item_id = item_exists(
            abs_path=os.path.dirname(mv_args.dest), db=db)

        if not parent_dest_exists:
            raise ValueError(f'mv: no such file or directory: {mv_args.dest}')

        # check if destination item exists
        dest_exists, dest_item_id = item_exists(
            abs_path=mv_args.dest, db=db)
        if dest_exists:
            dest_item_is_dir = with_row_locks(db.session.query(
                Item.is_dir)).filter(Item.id == dest_item_id).first()
            if dest_item_is_dir:
                # a directory
                # move src item to new_parent_id
                move_item(id=mv_args.srcs_id[0],
                          new_parent_id=dest_item_id, db=db)
            else:  # else dest_item = file
                # delete destination file
                delete_item(id=dest_item_id, db=db)
                # insert new file in the same parent directory as the deleted destination file
                move_item(
                    id=mv_args.src_id[0], new_parent_id=parent_dest_item_id, db=db)
        else:
            # TODO: still uncertain about whether I understood this requirement correctly
            # move the src to the parent_destination folder
            move_item(id=mv_args.src_id[0],
                      new_parent_id=parent_dest_item_id, db=db)
    else:  # many sources
        dest_exists, dest_item_id = item_exists(
            abs_path=mv_args.dest, db=db)

        if not dest_exists:
            raise ValueError(
                f'mv: no such destination file or directory: {mv_args.dest}')
        dest_item_is_dir = with_row_locks(db.session.query(
            Item.is_dir)).filter(Item.id == dest_item_id).first()

        if not dest_item_is_dir:
            raise ValueError(
                f'mv: no such destination directory: {mv_args.dest}')

        for src_id in mv_args.srcs_id:
            move_item(id=src_id, new_parent_id=dest_item_id, db=db)

    db.session.commit()
