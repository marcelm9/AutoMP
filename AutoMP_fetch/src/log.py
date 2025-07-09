import os
from time import strftime

from rich import print
from rich.progress import BarColumn, Progress


class Log:
    debug_mode = False

    @staticmethod
    def _color(message: str, color: str):
        return f"[{color}]{message}[/{color}]"

    @staticmethod
    def _brackets(message: str):
        return f"|{message}|"

    @staticmethod
    def _bold(message: str):
        return f"[bold]{message}[/bold]"

    @staticmethod
    def set_debug_mode(boolean: bool):
        Log.debug_mode = boolean

    @staticmethod
    def info(message: str):
        print(
            f"{Log._color('AutoMP_fetch', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'white')}"
        )

    @staticmethod
    def error(message: str):
        print(
            f"{Log._color('AutoMP_fetch', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'red')}"
        )

    @staticmethod
    def success(message: str):
        print(
            f"{Log._color('AutoMP_fetch', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'green')}"
        )

    @staticmethod
    def debug(message: str):
        if Log.debug_mode:
            print(
                f"{Log._color('AutoMP_fetch', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'grey30')}"
            )

    @staticmethod
    def get_summary(
        iteration: int, repeat_count: int | None, success_count: int, total: int
    ):
        message = ""
        if iteration != 0:
            message += f"(#{iteration}"
            if repeat_count is not None:
                message += f"/{repeat_count}"
            message += ") "
        message += f"Success rate: {success_count}/{total} ({round(success_count / total * 100, 1)}%)"
        return message

    @staticmethod
    def get_description(iteration: int, repeat_count: int | None, total_queries: int):
        message = ""
        if iteration != 0:
            message += f"(#{iteration}"
            if repeat_count is not None:
                message += f"/{repeat_count}"
            message += ") "
        message += f"Running {total_queries} queries"
        return message

    @staticmethod
    def progress():
        return Progress(
            f"{Log._color('AutoMP_fetch', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} |",
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
        )

    @staticmethod
    def logfile_write(log_directory: str, message: str):
        timestamp_str = strftime("%Y%m%d%H%M%S")
        with open(os.path.join(log_directory, "log.txt"), "a") as f:
            f.write(f"{timestamp_str} {message}\n")

    @staticmethod
    def logfile_write_fetch(
        log_directory: str,
        timestamp: str,
        taskname: str,
        model: str,
        success: bool,
        message: str,
    ):
        with open(os.path.join(log_directory, "log.txt"), "a") as f:
            f.write(
                f"{timestamp};{'SUCCESS' if success else 'FAILURE'};{taskname};{model};{message}\n"
            )
