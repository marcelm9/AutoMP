import os
from time import strftime

from rich import print


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
            f"{Log._color('AutoMP_test', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'white')}"
        )

    @staticmethod
    def error(message: str):
        print(
            f"{Log._color('AutoMP_test', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'red')}"
        )

    @staticmethod
    def success(message: str):
        print(
            f"{Log._color('AutoMP_test', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'green')}"
        )

    @staticmethod
    def debug(message: str):
        if Log.debug_mode:
            print(
                f"{Log._color('AutoMP_test', 'purple')} @ {Log._color(Log._bold(strftime('%Y-%m-%d %H:%M:%S')), 'cyan')} | {Log._color(message, 'grey30')}"
            )

    @staticmethod
    def logfile_write(log_directory: str, message: str):
        timestamp_str = strftime("%Y%m%d%H%M%S")
        with open(os.path.join(log_directory, "log.txt"), "a") as f:
            f.write(f"{timestamp_str};{message}\n")

    @staticmethod
    def logfile_write_test(
        log_directory: str, filename: str, status: bool, message: str
    ):
        timestamp_str = strftime("%Y%m%d%H%M%S")
        with open(os.path.join(log_directory, "log.txt"), "a") as f:
            f.write(
                f"{timestamp_str};{'SUCCESS' if status else 'FAILURE'};{filename};{message}\n"
            )
