import os
import subprocess
import sys

from ruamel.yaml import YAML

import src.error as e

from .log import Log
from .util import normalize_path


def _validate(
    data: dict,
    key: str,
    required: bool,
    type_: type | tuple[type],
    dependency: str = None,
) -> list[str]:
    if required and key not in data:
        return [e.missing_item(key)]
    if key in data and not isinstance(data[key], type_):
        if isinstance(type_, tuple):
            return [
                e.type_error(
                    key,
                    ", ".join([t.__name__ for t in type_]),
                    type(data[key]).__name__,
                )
            ]
        return [e.type_error(key, type_.__name__, type(data[key]).__name__)]
    if key in data and dependency is not None and dependency not in data:
        return [e.missing_dependency(key, dependency)]
    return []


class Validator:
    __path: str | None = None

    @staticmethod
    def validate(path, target_file: str | None) -> tuple[list[str], dict]:
        yaml = YAML(typ="safe")
        try:
            with open(path, "r") as file:
                data = yaml.load(file)
        except Exception as e:
            Log.error("Failed to load YAML file: " + str(e))
            sys.exit(1)
        Validator.__path = os.path.dirname(path)

        errors = []
        errors.extend(Validator.__validate_compiler_command(data))
        errors.extend(Validator.__validate_input(data, target_file))
        errors.extend(Validator.__validate_output_directory(data))
        errors.extend(Validator.__validate_compilation_directory(data))
        errors.extend(Validator.__validate_compiler_flags_macro(data))
        errors.extend(Validator.__validate_necessary_compiler_flags(data))
        errors.extend(Validator.__validate_args(data))
        errors.extend(Validator.__validate_repeat(data))
        errors.extend(Validator.__validate_overwrite_output(data))

        return errors, data

    @staticmethod
    def __validate_compiler_command(data) -> list[str]:
        errors = _validate(data, "compiler-command", True, str)
        if errors:
            return errors

        try:
            subprocess.check_call(
                [data["compiler-command"], "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except Exception:
            return [
                e.generic_error(
                    f"compiler-command error: running '{data['compiler-command']} -v' failed"
                )
            ]

        return []

    @staticmethod
    def __validate_input(data, target_file):
        errors = []
        errors.extend(Validator.__validate_input_directory(data))
        errors.extend(Validator.__validate_target_file(target_file))

        if errors:
            return errors
        elif "input-directory" not in data and target_file is None:
            return [e.missing_item("input-directory")]

        if target_file is None:
            path = normalize_path(data["input-directory"], Validator.__path)
            if not os.listdir(path):
                return [e.value_error("input-directory", path, "directory is empty")]
        else:
            data["__target-file"] = target_file

        return []

    @staticmethod
    def __validate_target_file(target_file) -> list[str]:
        if target_file is None:
            return []

        if not os.path.exists(target_file):
            return [e.cli_input_error(f"target file '{target_file}' does not exist")]

        if not os.path.isfile(target_file):
            return [e.cli_input_error(f"target file '{target_file}' is not a file")]

        if len(os.path.basename(target_file).split("__")) != 3:
            return [
                e.cli_input_error(
                    f"target file '{target_file}' has invalid name (need format DATE__TASKNAME__LLM)"
                )
            ]

        return []

    @staticmethod
    def __validate_input_directory(data) -> list[str]:
        errors = _validate(data, "input-directory", False, str)
        if errors:
            return errors

        path = normalize_path(data["input-directory"], Validator.__path)

        if not os.path.exists(path):
            return [e.value_error("input-directory", path, "path does not exist")]

        if not os.path.isdir(path):
            return [
                e.value_error(
                    "input-directory",
                    path,
                    "path is not a directory",
                )
            ]

        # check if all files follow the form DATE__TASKNAME__LLM
        invalid_files = [
            f.name
            for f in os.scandir(path)
            if len(f.name.split("__")) != 3 and f.name != "log.txt"
        ]
        if invalid_files:
            return [
                e.value_error(
                    "input-directory",
                    path,
                    f"invalid file names: {invalid_files}, need format DATE__TASKNAME__LLM",
                )
            ]

        return []

    @staticmethod
    def __validate_output_directory(data) -> list[str]:
        errors = _validate(data, "output-directory", True, str)
        if errors:
            return errors

        path = normalize_path(data["output-directory"], Validator.__path)

        if not os.path.exists(path):
            return [e.value_error("output-directory", path, "path does not exist")]

        if not os.path.isdir(path):
            return [
                e.value_error(
                    "output-directory",
                    path,
                    "path is not a directory",
                )
            ]

        # check write permissions
        if not os.access(path, os.W_OK):
            return [
                e.value_error(
                    "output-directory",
                    path,
                    "path is not writeable",
                )
            ]

        # check if directory is empty
        if len(os.listdir(path)) > 0:
            if not data.get("overwrite-output", False):
                return [
                    e.value_error(
                        "output-directory",
                        path,
                        "directory is not empty (add 'overwrite-output: true' to the config file to possibly overwrite existing files)",
                    )
                ]

        return []

    @staticmethod
    def __validate_compilation_directory(data) -> list[str]:
        errors = _validate(data, "compilation-directory", True, str)
        if errors:
            return errors

        path = normalize_path(data["compilation-directory"], Validator.__path)

        if not os.path.exists(path):
            return [
                e.value_error(
                    "compilation-directory",
                    path,
                    "path does not exist",
                )
            ]

        if not os.path.isdir(path):
            return [
                e.value_error(
                    "compilation-directory",
                    path,
                    "path is not a directory",
                )
            ]

        # check write permissions
        if not os.access(path, os.W_OK):
            return [
                e.value_error(
                    "compilation-directory",
                    path,
                    "path is not writeable",
                )
            ]

        return []

    @staticmethod
    def __validate_compiler_flags_macro(data) -> list[str]:
        return _validate(data, "compiler-flags-macro", True, str)

    @staticmethod
    def __validate_necessary_compiler_flags(data) -> list[str]:
        return _validate(data, "necessary-compiler-flags", False, list)

    @staticmethod
    def __validate_args(data) -> list[str]:
        errors = _validate(data, "args", True, dict)
        if errors:
            return errors

        return errors

    @staticmethod
    def __validate_repeat(data) -> list[str]:
        errors = _validate(data, "repeat", False, int)
        if errors:
            return errors

        if "repeat" in data and int(data["repeat"]) < 1:
            return [e.value_error("repeat", data["repeat"], "value has to be above 0")]

        return []

    @staticmethod
    def __validate_overwrite_output(data) -> list[str]:
        errors = _validate(data, "overwrite-output", False, bool)
        if errors:
            return errors

        return []
