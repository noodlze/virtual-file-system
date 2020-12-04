from collections import namedtuple
from cmd.db_helpers import list_child_items
from flask import session
from const import PARENT_ID

LS_CMD = "ls_cmd"
LS_RE = r'^ls( -l)*( \d+)*$'  # LS -l [LEVEL]
LsArgs = namedtuple("LsArgs", ["is_verbose", "level"])


def validate_ls_cmd_args(match, db):
    is_verbose = True if match.group(1) else False
    level = int(match.group(2)) if match.group(2) else 1

    return LsArgs(is_verbose, level)

# hack for server to pretty print file structure


def dir_tree_structure(dir_contents, is_verbose=False):
    lines = []
    lines.append(f'Total : {len(dir_contents)}')

    if len(dir_contents) == 0:
        return lines

    # add header
    name_header = "name".ljust(40, ' ')
    header = f'{name_header}'
    if is_verbose:
        created_at_header = "created_at".rjust(30, ' ')
        updated_at_header = "updated_at".rjust(30, ' ')
        size_header = "size".rjust(10, ' ')
        header = f'{created_at_header}{updated_at_header}{size_header}     ' + header
    lines.append(header)

    # add a row for each item in the folder

    for i, (ancestor, item) in enumerate(dir_contents):
        print(ancestor.rank)
        level = ancestor.rank.count(',')

        is_directory = item.is_dir
        if is_directory:  # a directory
            indent = ' ' * 4 * (level)
        else:
            indent = ' ' * 4 * (level + 1)

        # print(f'level={level},indent={indent},item={item.name}')

        details = ''
        if is_verbose:
            created_at = item.created_at.isoformat().rjust(30, ' ')
            updated_at = item.updated_at.isoformat().rjust(30, ' ')
            size = str(item.size).rjust(10, ' ')
            details += f'{created_at}{updated_at}{size}'

        lines.append('{}{}{}{}'.format(details, indent,
                                       item.name,
                                       "/" if is_directory else ""))

    return lines


def execute_ls_cmd(ls_args, db):
    # in  hierarchical order
    print("execute_ls_cmd")
    print("PARENT_ID =", session.get(PARENT_ID, None))
    folder_contents = list_child_items(
        parent_id=session.get(PARENT_ID, 0), depth=ls_args.level, db=db)

    resp = {
        "response": dir_tree_structure(folder_contents, ls_args.is_verbose)
    }

    return resp
