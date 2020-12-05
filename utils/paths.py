import os
from flask import session
from const import PARENT_ID, PARENT_ABS_PATH


def to_abs_path(path):
    # determine whether abs/relative path
    # works even if it contains asterisk
    # abs path == one that begins with /
    # relative path = relative to current directory on terminal

    if not os.path.isabs(path):
        cur_dir = session.get(PARENT_ABS_PATH, "/")
        abs_path = os.path.join(cur_dir, path)

    # resolve aliases . and .. and /(at the end) if present
    return os.path.normpath(abs_path)
