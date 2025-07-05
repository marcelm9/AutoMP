import argparse
import os
import sys

from src.automp_test import AutoMP_test
from src.log import Log
from src.validator import Validator

parser = argparse.ArgumentParser()
parser.add_argument(
    "-c",
    "--config",
    type=str,
    default="automp_test.yaml",
    help="path to the configuration file",
)
parser.add_argument(
    "-t",
    "--target",
    type=str,
    default=None,
    help="path to the target file",
)

args = parser.parse_args()
config_path = args.config
target_file = args.target

if not os.path.exists(config_path) or not os.path.isfile(config_path):
    Log.error(f"Configuration file '{config_path}' not found")
    sys.exit(1)

errors, data = Validator.validate(config_path, target_file)

if errors:
    Log.error(f"Configuration invalid. Error{'s' if len(errors) > 1 else ''}:")
    for e in errors:
        Log.info(e)
    sys.exit(1)
else:
    Log.success("Configuration valid")

AutoMP_test(os.path.dirname(config_path), data)
