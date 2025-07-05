import argparse
import os
import sys

from src.automp_fetch import AutoMP_fetch
from src.log import Log
from src.validator import Validator

parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--config",
    type=str,
    default="automp_fetch.yaml",
    help="path to the configuration file",
)

args = parser.parse_args()
config_path = args.config

if not os.path.exists(config_path) or not os.path.isfile(config_path):
    Log.error(f"Configuration file '{config_path}' not found")
    sys.exit(1)

Log.info("AutoMP_fetch started")

errors, data = Validator.validate(config_path)

if errors:
    Log.error(f"Configuration invalid. Error{'s' if len(errors) > 1 else ''}:")
    for e in errors:
        Log.info(e)
    sys.exit(1)
else:
    Log.success("Configuration valid")


AutoMP_fetch(os.path.dirname(config_path), data)
