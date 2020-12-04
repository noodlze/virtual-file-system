import os
from models import db
from flask import session
from blueprints import PARENT_ID, PARENT_ABS_PATH


def clean_re_group(s):
    # strip leading and trailing spaces
    # remove parethesis '/ "
    return s.rstrip().replace("'", "").replace('"', '')


def to_abs_path(path):
    # determine whether abs/relative path
    # works even if it contains asterisk
    # abs path == one that begins with /
    # relative path = relative to current directory on terminal
    abs_path = clean_re_group(path)

    if not os.path.isabs(path):
        cur_dir = session[PARENT_ABS_PATH]
        abs_path = os.path.join(cur_dir, path)

    # resolve aliases . and .. and /(at the end) if present
    return os.path.normpath(abs_path)
