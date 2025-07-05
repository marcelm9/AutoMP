import json
import os
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from cron_descriptor import get_description
from croniter import croniter

import src.cron as cron
from src.job import Job
from src.log import Log
from src.models import Models
from src.pushover import Pushover


class AutoMP_fetch:
    def __init__(self, config_file_dir, data):
        signal.signal(signal.SIGINT, self.__early_shutdown)

        self._job = Job(config_file_dir, data)
        Log.logfile_write(self._job.get_log_directory(), "started")
        Log.set_debug_mode(self._job.get_debug())
        if self._job.get_notifications_active():
            self._pushover = Pushover(self._job)
            self._pushover.perform_check()
        self._models = Models(self._job)

        self._iterations = 0

        if self._job.get_repeat() is None:
            Log.info("Running once")
            self.__act(datetime.now())
            self.__end()
        else:
            self._models.perform_check()  # we do not need a check if we only query once
            Log.info(
                f"Starting cron job: {get_description(self._job.get_repeat()).lower()}"
            )
            if self._job.get_repeat_count() is not None:
                Log.info(f"Running {self._job.get_repeat_count()} iterations")

            if self._job.get_notifications_active():
                Log.info(f"Notifications {Log._color('ON', 'green')}")
            else:
                Log.info(f"Notifications {Log._color('OFF', 'red')}")
            self._croniter = croniter(self._job.get_repeat())
            self.__mainloop()

    def __mainloop(self):
        while True:
            next_run: datetime = self._croniter.get_next(datetime, datetime.now())
            if self._job.has_repeat_end() and next_run >= self._job.get_repeat_end():
                Log.info("Next run is past repeat end")
                self.__end()
            Log.info(f"Next run: {self._croniter.get_next(datetime, datetime.now())}")
            cron.wait_for_datetime(next_run)
            self._iterations += 1
            self.__act(next_run)
            if (
                self._job.has_repeat_count()
                and self._iterations >= self._job.get_repeat_count()
            ):
                Log.info("Repeat count reached")
                self.__end()

    def __act(self, timestamp: datetime):
        with Log.progress() as progress:
            total_queries = len(self._job.get_tasks()) * len(self._job.get_models())
            progress_bar_task = progress.add_task(
                Log.get_description(
                    self._iterations, self._job.get_repeat_count(), total_queries
                ),
                total=total_queries,
            )

            if self._job.get_threading():
                futures = []
                with ThreadPoolExecutor() as executor:
                    for task in self._job.get_tasks():
                        for model in self._job.get_models():
                            futures.append(
                                executor.submit(
                                    self._models.query,
                                    model,
                                    timestamp,
                                    task["name"],
                                    task["prompt"],
                                    task["code"],
                                )
                            )
                    for future in as_completed(futures):
                        future.result()
                        progress.update(progress_bar_task, advance=1)
            else:
                for task in self._job.get_tasks():
                    for model in self._job.get_models():
                        self._models.query(
                            model, timestamp, task["name"], task["prompt"], task["code"]
                        )
                        progress.update(progress_bar_task, advance=1)

        self.__check_stats_and_notify(timestamp)

    def __check_stats_and_notify(self, timestamp: datetime):
        timestamp_str = timestamp.strftime("%Y%m%d%H%M%S")
        paths = [
            f
            for f in os.listdir(self._job.get_log_directory())
            if f.startswith(timestamp_str) and f.endswith(".json")
        ]
        total = len(paths)
        if total == 0:
            return

        success_count = 0
        for path in paths:
            with open(os.path.join(self._job.get_log_directory(), path), "r") as file:
                data = json.load(file)
            if data.get("request_success", False) and data.get(
                "parsing_success", False
            ):
                success_count += 1

        message = Log.get_summary(
            self._iterations, self._job.get_repeat_count(), success_count, total
        )

        if success_count < total:
            if self._job.get_notifications_active():
                self._pushover.send(message)
            Log.error(message)

        else:
            if (
                self._job.get_notifications_active()
                and self._job.get_notify_on_success()
            ):
                self._pushover.send(message)
            Log.info(message)

    def __early_shutdown(self, signum, frame):
        if self._job.get_notifications_active():
            self._pushover.send("AutoMP_fetch is shutting down")
        print()
        Log.info("Shutting down gracefully...")
        sys.exit(0)

    def __end(self):
        if self._job.get_notifications_active():
            self._pushover.send("AutoMP_fetch is done")
        Log.logfile_write(self._job.get_log_directory(), "ended")
        sys.exit(0)
