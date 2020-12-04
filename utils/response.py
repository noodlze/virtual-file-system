import functools
import logging
import json
from flask import current_app  # TODO: learn about this


def terminal_prefix(cur_dir):
    return f'{cur_dir} >'


def format_response(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            success_response = {
                "code": 0,
                "data": func(*args, **kwargs)
            }

            current_app.logger.debug(
                "Success reponse JSON %s" % json.dumps(success_response))

            return success_response

        except Exception as e:
            logging.exception(e)
            err_resp = {
                "code": 1,
                "data": {
                    "err": str(e)
                }
            }
            current_app.logger.debug(
                "Failed reponse JSON %s" % json.dumps(err_resp))
            return err_resp

    return wrapper
