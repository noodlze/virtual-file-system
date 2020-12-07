import re
import os
import argparse
from utils.paths import to_abs_path
from cmd.db_helpers import delete_item, item_exists, move_item, with_row_locks, to_abs_path_ids, item_exists_in_folder, resolve_asterisk_in_abs_path
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

    # deal with asterisks/wildcards
    abs_srcs_no_wildcards = []
    for abs_src_path in abs_srcs:
        # a list of tuples
        _abs_path_parts_list = resolve_asterisk_in_abs_path(abs_src_path)
        abs_srcs_no_wildcards.extend(_abs_path_parts_list)

    for name_parts, id_parts in abs_srcs_no_wildcards:
        if -1 in id_parts:
            raise ValueError(
                f'mv: no such file(s) or directory(ies): {"/".join(name_parts)}')

    abs_srcs_paths = ["/".join(_src[0]) for _src in abs_srcs_no_wildcards]
    abs_srcs_path_ids = [_src[1][-1] for _src in abs_srcs_no_wildcards]

    dest = cmd_args[-1]
    abs_dest = to_abs_path(dest)

    return MvArgs(srcs=abs_srcs_paths, srcs_id=abs_srcs_path_ids, dest=abs_dest)


@provide_db_session
def execute_mv_cmd(mv_args, db=None):
    if len(mv_args.srcs) == 1:
        print("only 1 src")

        dest_path_parts, dest_path_parts_id = to_abs_path_ids(mv_args.dest)

        # check if parent folder exists
        if -1 in dest_path_parts_id[:-1]:
            raise ValueError(f'mv: no such file or directory: {mv_args.dest}')

        parent_dest_item_id = dest_path_parts_id[-2]
        dest_item_id = dest_path_parts_id[-1]

        if dest_item_id != -1:  # dest item exists
            dest_item_is_dir = with_row_locks(db.session.query(
                Item.is_dir).filter(Item.id == dest_item_id), of=Item).first()
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
            raise InvalidCmdError(
                "cmd `mv source destination` where destination doesn't exist hasn't been implemented yet.SRRY!...")
            # TODO
            # may require renaming file, which would entail deleting src file and adding new one
            # move_item(
            #     id=mv_args.srcs_id[0], new_parent_id=parent_dest_item_id)

    else:  # many sources

        dest_exists, dest_item_id = item_exists(
            abs_path=mv_args.dest)

        if not dest_exists:
            raise ValueError(
                f'mv: no such destination file or directory: {mv_args.dest}')
        dest_item_is_dir = with_row_locks(db.session.query(
            Item.is_dir).filter(Item.id == dest_item_id), of=Item).first()

        if not dest_item_is_dir:
            raise ValueError(
                f'mv: no such destination directory: {mv_args.dest}')

        for src_id in mv_args.srcs_id:
            move_item(id=src_id, new_parent_id=dest_item_id)

    resp = {
        "response": 'Moved:\n{}\n\t---->{}'.format("\n".join(mv_args.srcs), mv_args.dest)
    }
    return resp
