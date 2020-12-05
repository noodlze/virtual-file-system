
from cmd.cd import CD_RE, check_cd_cmd_args, execute_cd_cmd
from cmd.ls import LS_RE, check_ls_cmd_args, execute_ls_cmd
from cmd.cr import CR_RE, check_cr_cmd_args, execute_cr_cmd
from cmd.mv import MV_RE, check_mv_cmd_args, execute_mv_cmd
from cmd.rm import RM_RE, check_rm_cmd_args, execute_rm_cmd
from cmd.h import check_help_cmd_args
from utils.response import InvalidCmdError


def validate_args_len(cmd, cmd_args, min_len=None, max_len=None, exact_len=None):
    """
    """
    if exact_len and len(cmd_args) != exact_len:
        # print usage
        raise InvalidCmdError(
            message=f'{cmd}: Expected 1 folder arg, got {len(cmd_args)}: {" ".join(cmd_args)}')

    if min_len and len(cmd_args) < min_len:
        # print usage
        raise InvalidCmdError(
            message=f'{cmd}: Expected at least {min_len} args, got {len(cmd_args)} args: {" ".join(cmd_args)}')

    if max_len and len(cmd_args) > max_len:
        raise InvalidCmdError(
            message=f'{cmd}: Expected most {max_len} args, got {len(cmd_args)} args: {" ".join(cmd_args)}')
    

CD_CMD = "cd"
LS_CMD = "ls"
CR_CMD = "cr"
MV_CMD = "mv"
RM_CMD = "rm"
HELP_CMD = "--help"

VALID_COMMANDS = [CD_CMD, LS_CMD, CR_CMD, MV_CMD, RM_CMD, HELP_CMD]

CMD_ARGS_CHECKER = {
    CD_CMD: check_cd_cmd_args,
    LS_CMD: check_ls_cmd_args,
    CR_CMD: check_cr_cmd_args,
    MV_CMD: check_mv_cmd_args,
    RM_CMD: check_rm_cmd_args,
    HELP_CMD: check_help_cmd_args,
}

CMD_PARSER = {
    CD_CMD: check_cd_cmd_args,
    LS_CMD: check_ls_cmd_args,
    CR_CMD: check_cr_cmd_args,
    MV_CMD: check_mv_cmd_args,
    RM_CMD: check_rm_cmd_args,
}

CMD_EXECUTOR = {
    CD_CMD: execute_cd_cmd,
    LS_CMD: execute_ls_cmd,
    CR_CMD: execute_cr_cmd,
    MV_CMD: execute_mv_cmd,
    RM_CMD: execute_rm_cmd,
}
