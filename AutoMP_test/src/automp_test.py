import json
import os
import platform
import subprocess
import time
from dataclasses import dataclass

from tabulate import tabulate

from .log import Log
from .util import normalize_path


@dataclass
class Run:
    exit_code: int = None
    run_time: float = None
    output: str = None

    def to_dict(self):
        return {
            "exit_code": self.exit_code,
            "run_time": self.run_time,
            "output": self.output,
        }

    @staticmethod
    def from_dict(data):
        run = Run()
        run.exit_code = data["exit_code"]
        run.run_time = data["run_time"]
        run.output = data["output"]
        return run


@dataclass
class Task:
    path: str = None
    date: str = None
    taskname: str = None
    llm: str = None
    errors: list[str] = None
    flags: list[str] = None
    compilation_time: float = None
    executable_path: str = None
    args: list[str] = None
    runs: dict[str, Run] = None
    system: dict = None

    def save_into_directory(self, directory: str):
        with open(
            os.path.join(directory, f"{os.path.basename(self.path)}.json"), "w"
        ) as f:
            json.dump(
                {
                    "system": self.system,
                    "path": self.path,
                    "date": self.date,
                    "taskname": self.taskname,
                    "llm": self.llm,
                    "errors": self.errors,
                    "flags": self.flags,
                    "compilation_time": self.compilation_time,
                    "executable_path": self.executable_path,
                    "args": self.args,
                    "runs": {k: [r.to_dict() for r in v] for k, v in self.runs.items()},
                },
                f,
                indent=4,
            )

    @staticmethod
    def from_dict(data):
        task = Task()
        task.path = data["path"]
        task.date = data["date"]
        task.taskname = data["taskname"]
        task.llm = data["llm"]
        task.errors = data["errors"]
        task.flags = data["flags"]
        task.compilation_time = data["compilation_time"]
        task.executable_path = data["executable_path"]
        task.args = data["args"]
        task.runs = {k: [Run.from_dict(r) for r in v] for k, v in data["runs"].items()}
        task.system = data["system"]
        return task


@dataclass
class MyPosixDirEntry:
    name: str
    path: str


class AutoMP_test:
    def __init__(self, config_file_dir, data):
        self._compiler_command = data["compiler-command"]
        self._input_directory = (
            normalize_path(data["input-directory"], config_file_dir)
            if "input-directory" in data
            else None
        )
        self._output_directory = normalize_path(
            data["output-directory"], config_file_dir
        )
        Log.logfile_write(self._output_directory, "started")
        self._compilation_directory = normalize_path(
            data["compilation-directory"], config_file_dir
        )
        self._compiler_flags_macro = data["compiler-flags-macro"]
        self._necessary_compiler_flags = data.get("necessary-compiler-flags", [])
        self._repeat = data.get("repeat", 1)
        self._args: dict = data["args"]
        self._timeout = data.get("timeout", 60)

        target_file = data.get("__target-file", None)
        if target_file is not None:
            self.__target_file = MyPosixDirEntry(
                os.path.basename(target_file), target_file
            )
        else:
            self.__target_file = None

        self.__run()

        Log.logfile_write(self._output_directory, "ended")

    def __get_system_info(self):
        # get memory information in bytes
        # os.sysconf("SC_PAGE_SIZE") gives the page size in bytes
        # os.sysconf("SC_PHYS_PAGES") gives the number of physical pages
        total_memory_bytes = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")

        system_info = {
            "system": platform.system(),
            "node_name": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_build": f"{platform.python_build()[0]} {platform.python_build()[1]}",
            "cpu_count": os.cpu_count(),
            "total_memory_bytes": total_memory_bytes,
        }
        return system_info

    def __run(self):
        for file in ([self.__target_file] if self.__target_file is not None else []) + (
            [
                f
                for f in os.scandir(self._input_directory)
                if f.is_file() and f.name.endswith(".c")
            ]
            if self._input_directory is not None
            else []
        ):
            Log.info(f"Processing {file.name}")
            current = Task()
            current.system = self.__get_system_info()
            current.errors = []
            current.runs = {}
            current.path = file.path
            current.date, current.taskname, current.llm = os.path.basename(
                file.path
            ).split("__", 2)
            if ":" in current.llm:
                current.llm = current.llm.split(":")[0]
            if current.llm.endswith(".c"):
                current.llm = current.llm.removesuffix(".c")

            # get arguments from yaml
            if (
                current.taskname not in self._args.keys()
                or len(self._args[current.taskname]) == 0
            ):
                current.errors.append(f"No arguments found for '{current.taskname}'")
                current.save_into_directory(self._output_directory)
                Log.error("  No arguments found")
                Log.logfile_write_test(
                    self._output_directory, current.path, False, "no arguments found"
                )
                continue
            current.args = self._args[current.taskname]

            # check if necessary flags are present
            current.flags = self.__extract_flags(file.path)
            if self._necessary_compiler_flags is not None:
                for flag in self._necessary_compiler_flags:
                    if flag not in current.flags:
                        current.errors.append(
                            f"Missing necessary compiler flag: '{flag}'"
                        )
            if current.errors:
                current.save_into_directory(self._output_directory)
                Log.error("  Missing necessary compiler flag(s)")
                Log.logfile_write_test(
                    self._output_directory,
                    current.path,
                    False,
                    "missing necessary compiler flag",
                )
                continue

            Log.info("  Passed checks")

            # compile and check for compilation errors
            exit_code, compilation_output, executable_path, duration = self.__compile(
                file, current.flags
            )
            if exit_code != 0:
                current.errors.append(f"Compilation error: {compilation_output}")
                current.save_into_directory(self._output_directory)
                Log.error("  Compilation error")
                Log.logfile_write_test(
                    self._output_directory,
                    current.path,
                    False,
                    f"compilation error (exit code: {exit_code})",
                )
                continue
            current.compilation_time = duration
            current.executable_path = executable_path
            Log.info("  Compilation successful")

            # run with args
            current.runs = {}

            Log.info(f"  Running program with {len(current.args)} argument(s)")
            for i, arg in enumerate(current.args):
                Log.info(
                    f"    Performing {self._repeat} run(s) with argument(s) '{arg}'"
                )
                runs: list[Run] = []
                for j in range(self._repeat):
                    exit_code, output, duration = self.__run_executable(
                        executable_path, arg
                    )
                    run = Run()
                    run.exit_code = exit_code
                    run.run_time = duration
                    run.output = output
                    runs.append(run)

                    Log.debug(f"      {j + 1} / {self._repeat}")
                current.runs[arg] = runs
                Log.debug(f"    {i + 1} / {len(current.args)}")

            current.save_into_directory(self._output_directory)
            Log.logfile_write_test(self._output_directory, current.path, True, "")

    def __extract_flags(self, path):
        with open(path, "r") as f:
            lines = f.readlines()

        target_lines = [
            line
            for line in lines
            if line.startswith(f"#define {self._compiler_flags_macro}")
        ]
        if len(target_lines) == 0:
            return []

        flags_string = (
            target_lines[0]
            .removeprefix(f"#define {self._compiler_flags_macro}")
            .strip()
            .replace('"', "")
        )
        return flags_string.split(" ")

    def __compile(self, file: os.DirEntry, flags: list[str]):
        executable_path = os.path.join(
            self._compilation_directory, file.name.removesuffix(".c")
        )
        start_time = time.time()
        process = subprocess.run(
            [self._compiler_command, file.path, "-o", executable_path, *flags],
            capture_output=True,
            text=True,
        )
        end_time = time.time()
        exit_code = process.returncode
        compilation_output = process.stdout + process.stderr

        return exit_code, compilation_output, executable_path, end_time - start_time

    def __run_executable(self, executable_path: str, arg: str):
        try:
            process = subprocess.run(
                [executable_path, *arg.split(" ")],
                capture_output=True,
                text=True,
                timeout=self._timeout,
            )
            exit_code = process.returncode
            output = process.stdout + process.stderr
        except subprocess.TimeoutExpired:
            exit_code = -1
            output = "timeout"

        if exit_code == 0:
            _, run_time = json.loads(output)
        else:
            run_time = 0

        return exit_code, output, run_time
