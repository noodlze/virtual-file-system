import functools
import logging
import json
from flask import current_app  # TODO: learn about this


class InvalidCmdError(Exception):
    """
    Gives control over error response message displayed on the web UI
    If `ui_msg` param is passed:
        error response message sent back to client will differ from server error displayed
    else
        `ui_msg` will have same contents as `message`
    """

    def __init__(self, message, ui_msg=None):

        # Call the base class constructor with the parameters it needs
        super(InvalidCmdError, self).__init__(message)

        # terminal response message to be displayed on the web ui...
        if ui_msg:
            self.ui_msg = ui_msg
        else:
            self.ui_msg = message


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
