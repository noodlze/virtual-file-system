import re
import os
import argparse
from utils.paths import to_abs_path
from cmd.db_helpers import delete_item, item_exists, move_item, with_row_locks
from models.item import Item
from collections import namedtuple
from utils.response import InvalidCmdError
from utils.db_session import provide_db_session

MvArgs = namedtuple("MvArgs", ["srcs", "srcs_id", "dest"])
# mv SOURCE DESTINATION
# mv SOURCE... DESTINATION


@provide_db_session
def check_mv_cmd_args(cmd_args, db=None):
    # dummy parser, for printing usage doc purposes only
    # does not work as will incorrectly add destination to src arg
    mv_parser = argparse.ArgumentParser(
        description="move files/folders to another destination")

    mv_parser.add_argument('src', metavar='SOURCE', nargs='+')
    mv_parser.add_argument('dest', metavar='DESTINATION', nargs=1)

    if '-h' in cmd_args or '--help' in cmd_args:
        raise InvalidCmdError(message=mv_parser.format_help())

    if len(cmd_args) < 2:
        raise InvalidCmdError(
            message=f'mv: Expected at least 2 args, got {len(cmd_args)} args: {" ".join(cmd_args)}')

    srcs = cmd_args[:-1]
    # srcs may contain asterisks
    abs_srcs = [to_abs_path(path) for path in srcs]
    srcs_ids = []

    for s in abs_srcs:
        exists, item_id = item_exists(abs_path=s)

        if not exists:
            raise ValueError(f'mv: no such file or directory: {s}')

        srcs_ids.append(item_id)

    dest = cmd_args[-1]
    abs_dest = to_abs_path(dest)

    return MvArgs(abs_srcs, srcs_ids, abs_dest)


@provide_db_session
def execute_mv_cmd(mv_args, db=None):
    print("executing mv_cmd: srcs={},srcs_id={},dest={}".format(
        mv_args.srcs, mv_args.srcs_id, mv_args.dest))
    # TODO: deal with wildcards
    if len(mv_args.srcs) == 1:
        print("only 1 src")
        # check if parent folder exists
        parent_dest_exists, parent_dest_item_id = item_exists(
            abs_path=os.path.dirname(mv_args.dest))

        if not parent_dest_exists:
            raise ValueError(f'mv: no such file or directory: {mv_args.dest}')

        # check if destination item exists
        dest_exists, dest_item_id = item_exists(
            abs_path=mv_args.dest)
        if dest_exists:
            dest_item_is_dir = with_row_locks(db.session.query(
                Item.is_dir)).filter(Item.id == dest_item_id).first()
            if dest_item_is_dir:
                # a directory
                # move src item to new_parent_id
                move_item(id=mv_args.srcs_id[0],
                          new_parent_id=dest_item_id)
            else:  # else dest_item = file
                # delete destination file
                delete_item(id=dest_item_id)
                # insert new file in the same parent directory as the deleted destination file
                move_item(
                    id=mv_args.srcs_id[0], new_parent_id=parent_dest_item_id)
        else:
            # TODO: still uncertain about whether I understood this requirement correctly
            # move the src to the parent_destination folder
            move_item(id=mv_args.srcs_id[0],
                      new_parent_id=parent_dest_item_id)
    else:  # many sources
        dest_exists, dest_item_id = item_exists(
            abs_path=mv_args.dest)

        if not dest_exists:
            raise ValueError(
                f'mv: no such destination file or directory: {mv_args.dest}')
        dest_item_is_dir = with_row_locks(db.session.query(
            Item.is_dir)).filter(Item.id == dest_item_id).first()

        if not dest_item_is_dir:
            raise ValueError(
                f'mv: no such destination directory: {mv_args.dest}')

        for src_id in mv_args.srcs_id:
            move_item(id=src_id, new_parent_id=dest_item_id)
