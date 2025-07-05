import os
from datetime import datetime


class Job:
    """
    Job describes the configuration of AutoMP_fetch and provides useful methods
    to read data from the configuration.
    """

    def __init__(self, config_file_dir: str, data: dict):
        self._data = data

        # set default values here
        self._models = data.get("models")
        self._input = data.get("input")
        self._input_directive = data.get("input-directive", None)
        output_directory = data.get("output-directory")
        if os.path.isabs(output_directory):
            self._output_directory = output_directory
        else:
            self._output_directory = os.path.abspath(
                os.path.join(config_file_dir, output_directory)
            )
        self._repeat = data.get("repeat", None)
        self._repeat_count = data.get("repeat-count", None)
        self._repeat_end = data.get("repeat-end", None)
        self._pushover = data.get("pushover", None)
        self._openrouter_api_key = data.get("openrouter-api-key", None)
        if os.path.isabs(data.get("log-directory")):
            self._log_directory = data.get("log-directory")
        else:
            self._log_directory = os.path.abspath(
                os.path.join(config_file_dir, data.get("log-directory"))
            )
        self._notify_on_success = data.get("notify-on-success", False)
        self._threading = data.get("threading", False)
        self._debug = data.get("debug", False)
        self._max_attempts = data.get("max-attempts", 3)

        tasks = []
        for task, content in self._input.items():
            code = None
            if "file" in content:
                if os.path.isabs(content["file"]):
                    path = content["file"]
                else:
                    path = os.path.abspath(
                        os.path.join(config_file_dir, content["file"])
                    )
                with open(path, "r") as file:
                    code = file.read()
            elif "code" in content:
                code = content["code"]
            tasks.append(
                {
                    "name": task,
                    "prompt": content["prompt"],
                    "code": code,
                }
            )
        self._tasks = tasks

    def get_debug(self):
        return self._debug

    def get_openrouter_api_key(self):
        return self._openrouter_api_key

    def get_input_directive(self):
        return self._input_directive

    def has_input_directive(self):
        return self._input_directive is not None

    def get_output_directory(self):
        return self._output_directory

    def get_notifications_active(self):
        return self._pushover is not None

    def get_pushover(self) -> tuple[str, str, str]:
        if self._pushover is None:
            return None
        else:
            return (
                self._pushover["api-token"],
                self._pushover["user-token"],
                self._pushover.get("device", None),
            )

    def get_models(self):
        return self._models

    def get_tasks(self):
        return self._tasks

    def get_notify_on_success(self):
        return self._notify_on_success

    def get_repeat(self):
        return self._repeat

    def has_repeat_count(self):
        return self._repeat_count is not None

    def get_repeat_count(self):
        return self._repeat_count

    def has_repeat_end(self):
        return self._repeat_end is not None

    def get_repeat_end(self) -> datetime:
        return self._repeat_end

    def new_logfile(self, name: str, content: str):
        with open(f"{self._log_directory}/{name}.log", "w") as file:
            file.write(content)

    def get_threading(self):
        return self._threading

    def get_log_directory(self):
        return self._log_directory

    def get_max_attempts(self):
        return self._max_attempts
