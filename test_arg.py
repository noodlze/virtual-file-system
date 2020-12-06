import argparse
import sys

cr_parser = argparse.ArgumentParser(
    description="move files/folders to another destination")

cr_parser.add_argument('src', metavar='SOURCE', nargs='+')
# dummy arg, for usage doc purposes only
# destination = cmd_args[-1] and will not be passed to cr_parser
cr_parser.add_argument('dest', metavar='DESTINATION', nargs=1)

try:
    tests = [['-h'],
             ['/1/2/3', '2', '2/file'],
             [],
             ['-p', 'test path'],
             ]
    for t in tests:
        print(cr_parser.parse_args(t))
except SystemExit as e:
    print("raised system exit message")
    # if str(e) == "0":
    #     print("requested help")
    print(cr_parser.format_help())
    # print(cd_parser.format_help(), type(cd_parser.format_usage()))
    # print(str(e))

print("exited cleanly")
