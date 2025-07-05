import os
import sys
from datetime import date, datetime
from typing import Any

import src.error as e
from croniter import croniter
from ruamel.yaml import YAML
from src.cron import validate_cron
from src.log import Log


def _validate(
    data: dict,
    key: str,
    required: bool,
    type_: Any | tuple[Any],
    dependency: str | None = None,
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
    def validate(path) -> tuple[list[str], dict]:
        yaml = YAML(typ="safe")
        try:
            with open(path, "r") as file:
                data = yaml.load(file)
        except Exception as e:
            Log.error("Failed to load YAML file: " + str(e))
            sys.exit(1)
        Validator.__path = os.path.dirname(path)

        errors = []
        errors.extend(Validator.__validate_models(data))
        errors.extend(Validator.__validate_input(data))
        errors.extend(Validator.__validate_input_directive(data))
        errors.extend(Validator.__validate_output_directory(data))
        errors.extend(Validator.__validate_repeat(data))
        errors.extend(Validator.__validate_repeat_count(data))
        errors.extend(Validator.__validate_repeat_end(data))
        errors.extend(Validator.__validate_pushover(data))
        errors.extend(Validator.__validate_openrouter_api_key(data))
        errors.extend(Validator.__validate_log_directory(data))
        errors.extend(Validator.__validate_notify_on_success(data))
        errors.extend(Validator.__validate_threading(data))
        errors.extend(Validator.__validate_max_attempts(data))

        return errors, data

    @staticmethod
    def __validate_models(data) -> list[str]:
        errors = _validate(data, "models", True, list)
        if errors:
            return errors

        for model in data["models"]:
            if not isinstance(model, str):
                errors.append(e.type_error("models", "string", type(model).__name__))

        return errors

    @staticmethod
    def __validate_input(data) -> list[str]:
        errors = _validate(data, "input", True, dict)
        if errors:
            return errors

        for task_name, task_content in data["input"].items():
            if not isinstance(task_content, dict):
                errors.append(
                    e.type_error(
                        f"input.{task_name}", "dict", type(task_content).__name__
                    )
                )
                continue
            # prompt
            if "prompt" not in task_content:
                errors.append(e.missing_item(f"input.{task_name}.prompt"))
            elif not isinstance(task_content["prompt"], str):
                errors.append(
                    e.type_error(
                        f"input.{task_name}.prompt",
                        "str",
                        type(task_content["prompt"]).__name__,
                    )
                )

            # code and file
            inp_code = "code" in task_content
            inp_file = "file" in task_content
            if inp_code and inp_file:
                errors.append(
                    e.constraint_error(
                        f"input.{task_name}",
                        "XOR between 'code' and 'file'",
                        "found 'code' and 'file' items",
                    )
                )
                continue

            # code
            if inp_code:
                if not isinstance(task_content["code"], str):
                    errors.append(
                        e.type_error(
                            f"input.{task_name}.code",
                            "str",
                            type(task_content["code"]).__name__,
                        )
                    )

            # file
            if inp_file:
                if isinstance(task_content["file"], str):
                    if os.path.isabs(task_content["file"]):
                        path = task_content["file"]
                    else:
                        path = os.path.abspath(
                            os.path.join(Validator.__path, task_content["file"])
                        )
                    if not os.path.exists(path):
                        errors.append(
                            e.value_error(
                                f"input.{task_name}.file",
                                path,
                                "path does not exist",
                            )
                        )
                    elif not os.path.isfile(path):
                        errors.append(
                            e.value_error(
                                f"input.{task_name}.file",
                                path,
                                "path is not a file",
                            )
                        )
                else:
                    errors.append(
                        e.type_error(
                            f"input.{task_name}.file",
                            "str",
                            type(task_content["file"]).__name__,
                        )
                    )

        return errors

    @staticmethod
    def __validate_input_directive(data) -> list[str]:
        return _validate(data, "input-directive", False, str)

    @staticmethod
    def __validate_output_directory(data) -> list[str]:
        errors = _validate(data, "output-directory", True, str)
        if errors:
            return errors

        if os.path.isabs(data["output-directory"]):
            path = data["output-directory"]
        else:
            path = os.path.abspath(
                os.path.join(Validator.__path, data["output-directory"])
            )

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

        return []

    @staticmethod
    def __validate_repeat(data) -> list[str]:
        errors = _validate(data, "repeat", False, str)
        if errors:
            return errors

        if "repeat" in data:
            validate_result = validate_cron(data["repeat"])
            if not validate_result[0]:
                return [
                    e.value_error(
                        "repeat",
                        data["repeat"],
                        f"invalid cron expression: {validate_result[1]}",
                    )
                ]

        return []

    @staticmethod
    def __validate_repeat_count(data) -> list[str]:
        errors = _validate(data, "repeat-count", False, int, "repeat")
        if errors:
            return errors

        if "repeat-count" in data:
            if data["repeat-count"] < 0:
                return [
                    e.value_error("repeat-count", data["repeat-count"], "must be >= 0")
                ]

        return []

    @staticmethod
    def __validate_repeat_end(data) -> list[str]:
        errors = _validate(data, "repeat-end", False, (date, datetime), "repeat")
        if errors:
            return errors

        if "repeat-end" in data:
            if isinstance(data["repeat-end"], date) and not isinstance(
                data["repeat-end"], datetime
            ):
                data["repeat-end"] = datetime.combine(
                    data["repeat-end"], datetime.min.time()
                )
                Log.debug(
                    f"Converting repeat-end from date to datetime: {data['repeat-end'].strftime('%Y-%m-%d %H:%M:%S')}"
                )
            cron = croniter(data["repeat"])
            next_run: datetime = cron.get_next(datetime, datetime.now())
            if next_run > data["repeat-end"]:
                return [
                    e.value_error(
                        "repeat-end",
                        data["repeat-end"],
                        f"next iteration is past this datetime at {next_run.strftime('%Y-%m-%d %H:%M:%S')}",
                    )
                ]

        return []

    @staticmethod
    def __validate_pushover(data) -> list[str]:
        errors = _validate(data, "pushover", False, dict)
        if errors:
            return errors

        if "pushover" in data:
            errors = []

            keys = list(data["pushover"].keys())
            if "api-token" not in keys:
                errors.append(e.missing_item("pushover.api-token"))
            else:
                if not isinstance(data["pushover"]["api-token"], str):
                    errors.append(
                        e.type_error(
                            "pushover.api-token",
                            "str",
                            type(data["pushover"]["api-token"]).__name__,
                        )
                    )
            if "user-token" not in keys:
                errors.append(e.missing_item("pushover.user-token"))
            else:
                if not isinstance(data["pushover"]["user-token"], str):
                    errors.append(
                        e.type_error(
                            "pushover.user-token",
                            "str",
                            type(data["pushover"]["user-token"]).__name__,
                        )
                    )
            if "device" in keys:
                if not isinstance(data["pushover"]["device"], str):
                    errors.append(
                        e.type_error(
                            "pushover.device",
                            "str",
                            type(data["pushover"]["user-token"]).__name__,
                        )
                    )

            if errors:
                return errors

        return []

    @staticmethod
    def __validate_openrouter_api_key(data) -> list[str]:
        return _validate(data, "openrouter-api-key", True, str)

    @staticmethod
    def __validate_log_directory(data) -> list[str]:
        errors = _validate(data, "log-directory", True, str)
        if errors:
            return errors

        if os.path.isabs(data["log-directory"]):
            path = data["log-directory"]
        else:
            path = os.path.abspath(
                os.path.join(Validator.__path, data["log-directory"])
            )

        if not os.path.exists(path):
            return [e.value_error("log-directory", path, "path does not exist")]

        if not os.path.isdir(path):
            return [
                e.value_error(
                    "log-directory",
                    path,
                    "path is not a directory",
                )
            ]

        # check write permissions
        if not os.access(path, os.W_OK):
            return [
                e.value_error(
                    "log-directory",
                    data["log-directory"],
                    "path is not writeable",
                )
            ]

        return []

    @staticmethod
    def __validate_notify_on_success(data) -> list[str]:
        return _validate(data, "notify-on-success", False, bool, "pushover")

    @staticmethod
    def __validate_threading(data) -> list[str]:
        return _validate(data, "threading", False, bool)

    @staticmethod
    def __validate_max_attempts(data) -> list[str]:
        return _validate(data, "max-attempts", False, int)
