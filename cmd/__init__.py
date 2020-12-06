from cmd.cd import check_cd_cmd_args, execute_cd_cmd
from cmd.ls import check_ls_cmd_args, execute_ls_cmd
from cmd.cr import check_cr_cmd_args, execute_cr_cmd
from cmd.mv import check_mv_cmd_args, execute_mv_cmd
from cmd.rm import check_rm_cmd_args, execute_rm_cmd
from utils.response import InvalidCmdError


CD_CMD = "cd"
LS_CMD = "ls"
CR_CMD = "cr"
MV_CMD = "mv"
RM_CMD = "rm"

VALID_COMMANDS = [CD_CMD, LS_CMD, CR_CMD, MV_CMD, RM_CMD]

CMD_ARGS_CHECKER = {
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
