import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
from src.config import OPENROUTER_URL, QUERY_TIMEOUT_SECONDS, TEST_QUERY
from src.job import Job
from src.log import Log


class Models:
    def __init__(self, job: Job):
        self._job = job

    def perform_check(self):
        Log.info("Starting test queries")

        errors = False
        with Log.progress() as progress:
            total_queries = len(self._job.get_models())
            progress_bar_task = progress.add_task(
                f"Running {total_queries} test queries", total=total_queries
            )

            if self._job.get_threading():
                futures = []
                with ThreadPoolExecutor() as executor:
                    for model in self._job.get_models():
                        futures.append(
                            executor.submit(
                                self.__query,
                                model,
                                TEST_QUERY,
                                "",
                                "",
                                False,
                                False,
                            )
                        )

                    for future in as_completed(futures):
                        if not future.result():
                            errors = True
                            Log.error(f"Test query error for model '{model}'")
                        progress.update(progress_bar_task, advance=1)
            else:
                for model in self._job.get_models():
                    if not self.__query(
                        model,
                        TEST_QUERY,
                        time.strftime("%Y%m%d%H%M%S"),
                        "test-query",
                        True,
                        False,
                    ):
                        errors = True
                        Log.error(f"Test query error for model '{model}'")
                    progress.update(progress_bar_task, advance=1)

        if errors:
            Log.error(
                "At least one test query failed. Check the log files for more information."
            )
            sys.exit(1)
        Log.success("Test queries succeeded")

    def query(
        self,
        model: str,
        timestamp: datetime,
        task_name: str,
        prompt: str,
        code: str | None,
    ):
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")

        path = os.path.join(
            self._job.get_output_directory(),
            f"{timestamp_str}__{task_name}__{model}".replace("/", "_"),
        )
        if os.path.exists(path):
            Log.error(f"Output file '{path}' already exists")
            Log.logfile_write_fetch(
                self._job.get_log_directory(),
                timestamp_str,
                task_name,
                model,
                False,
                f"output file '{path}' already exists",
            )
            return

        query = ""
        if self._job.has_input_directive():
            query += self._job.get_input_directive() + "\n\n"
        query += prompt
        if code is not None:
            query += "\n\n" + code

        success, message = self.__query(
            model, query, timestamp_str, task_name, True, True
        )

        Log.logfile_write_fetch(
            self._job.get_log_directory(),
            timestamp_str,
            task_name,
            model,
            success,
            message,
        )

    def __query(
        self,
        model: str,
        content: str,
        timestamp_str: str,
        task_name: str,
        write_log: bool = True,
        write_output: bool = True,
    ):
        """Returns True if the request was successful, False otherwise; also returns a string during which phase the error occurred"""
        Log.debug(f"Starting query for model '{model}'")

        filename_log = os.path.join(
            self._job.get_log_directory(),
            f"{timestamp_str}__{task_name}__{model.replace('/', '_')}.json",
        )
        filename_output = os.path.join(
            self._job.get_output_directory(),
            f"{timestamp_str}__{task_name}__{model.replace('/', '_')}",
        )

        try:
            request_success, message, seconds = self.__request(model, content)

            if not request_success and self._job.get_max_attempts() > 1:
                attempts = 1
                while not request_success and attempts < self._job.get_max_attempts():
                    Log.debug(
                        f"Retrying query for model '{model}' (attempt {attempts}/{self._job.get_max_attempts()})"
                    )
                    request_success, message, seconds = self.__request(model, content)
                    attempts += 1

            if not request_success:
                Log.debug(f"Failed query for model '{model}' during request")
                if write_log:
                    self.__write_log(
                        filename_log,
                        request_success=request_success,
                        request_seconds=seconds,
                        request_error=message,
                    )
                if write_output:
                    self.__write_output(
                        filename_output, "[AutoMP_fetch] An error occurred"
                    )
                return False, "error during request"

            parsing_error = None
            try:
                text_response = json.loads(message)["choices"][0]["message"]["content"]
            except Exception:
                text_response = None
                parsing_error = (
                    "cannot find 'choices[0].message.content' in OpenRouter response"
                )

            if text_response is None:
                Log.debug(f"Failed query for model '{model}' during parsing")
                if write_log:
                    self.__write_log(
                        filename_log,
                        request_success=request_success,
                        request_seconds=seconds,
                        parsing_success=False,
                        parsing_error=parsing_error,
                        openrouter=message,
                    )
                if write_output:
                    self.__write_output(
                        filename_output, "[AutoMP_fetch] An error occurred"
                    )
                return False, "error during parsing"

            Log.debug(f"Completed query for model '{model}'")

            if write_log:
                try:
                    openrouter_content = json.loads(message)
                    openrouter_content["choices"][0]["message"]["content"] = (
                        "[AutoMP_fetch] See corresponding output file"
                    )
                except Exception:
                    openrouter_content = None
                self.__write_log(
                    filename_log,
                    request_success=request_success,
                    request_seconds=seconds,
                    parsing_success=True,
                    parsing_error=parsing_error,
                    openrouter=openrouter_content,
                )

            if write_output:
                self.__write_output(filename_output, text_response)

            return True, ""

        except Exception:
            return False, str(traceback.format_exc())

    def __write_output(self, output_filename: str, content: str):
        with open(output_filename, "w") as file:
            file.write(content)

    def __write_log(
        self,
        log_filename: str,
        request_success: bool = None,
        request_seconds: float = None,
        request_error: str = None,
        openrouter: dict = None,
        parsing_success: bool = None,
        parsing_error: str = None,
    ):
        with open(log_filename, "w") as file:
            json.dump(
                {
                    "request_success": request_success,
                    "request_seconds": request_seconds,
                    "request_error": request_error,
                    "openrouter": openrouter,
                    "parsing_success": parsing_success,
                    "parsing_error": parsing_error,
                },
                file,
                indent=4,
            )

    def __request(self, model: str, content: str) -> tuple[bool, str, float]:
        """
        Returns a tuple of a bool (whether the request was successful), a
        string (either the error message or the response content) and a float
        (the time the request took in seconds).
        """

        success = None
        message = None
        seconds = None

        start_time = time.time()

        try:
            response = requests.post(
                url=OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {self._job.get_openrouter_api_key()}",
                },
                data=json.dumps(
                    {
                        "model": model,
                        "messages": [{"role": "user", "content": content}],
                    }
                ),
                timeout=QUERY_TIMEOUT_SECONDS,
            )
            end_time = time.time()
            success = True
            message = response.text
        except Exception as e:
            end_time = time.time()
            success = False
            message = str(e)

        seconds = end_time - start_time

        return success, message, seconds
