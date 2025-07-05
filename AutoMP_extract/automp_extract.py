import sys

from src.automp_extract import AutoMP_extract
from src.log import Log
from src.validator import Validator

if len(sys.argv) < 2:
    Log.error("Usage: python automp_extract.py <command>")
    Log.info("To see all available commands, run:")
    Log.info("")
    Log.info("    python automp_extract.py commands")
    sys.exit(1)

match sys.argv[1]:
    case "commands":
        AutoMP_extract.list_commands()
    case "single":
        if Validator.single(sys.argv):
            AutoMP_extract.single(sys.argv[2], sys.argv[3])
    case "multiple":
        if Validator.multiple(sys.argv):
            AutoMP_extract.multiple(sys.argv[2], sys.argv[3])
    case _:
        Log.error(f"Unknown command '{sys.argv[1]}'")
        AutoMP_extract.list_commands()
