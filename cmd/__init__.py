
from cmd.cd import CD_RE, CD_CMD, validate_cd_cmd_args, execute_cd_cmd
from cmd.ls import LS_RE, LS_CMD, validate_ls_cmd_args, execute_ls_cmd
from cmd.cr import CR_RE, CR_CMD, validate_cr_cmd_args, execute_cr_cmd
from cmd.mv import MV_RE, MV_CMD, validate_mv_cmd_args, execute_mv_cmd
from cmd.rm import RM_RE, RM_CMD, validate_rm_cmd_args, execute_rm_cmd

FILE_NAME_RE = r'^[a-zA-Z0-9 _-]+$'

CMD_TYPE_MAP = [(CD_RE, CD_CMD),
                (LS_RE, LS_CMD),
                (CR_RE, CR_CMD),
                (MV_RE, MV_CMD),
                (RM_RE, RM_CMD)]

CMD_PARSER = {
    CD_CMD: validate_cd_cmd_args,
    LS_CMD: validate_ls_cmd_args,
    CR_CMD: validate_cr_cmd_args,
    MV_CMD: validate_mv_cmd_args,
    RM_CMD: validate_rm_cmd_args,
}

CMD_EXECUTOR = {
    CD_CMD: execute_cd_cmd,
    LS_CMD: execute_ls_cmd,
    CR_CMD: execute_cr_cmd,
    MV_CMD: execute_mv_cmd,
    RM_CMD: execute_rm_cmd,
}
