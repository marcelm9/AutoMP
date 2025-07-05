import os
import sys

from .extract import extract_code_blocks
from .log import Log


class AutoMP_extract:
    __cache = []

    @staticmethod
    def list_commands():
        Log.info("Available commands:")
        Log.info("    commands")
        Log.info("    single <filepath_in> <filepath_out>")
        Log.info("    multiple <directory_in> <directory_out>")
        sys.exit(0)

    @staticmethod
    def single(filepath_in: str, filepath_out: str):
        log_dir = os.path.dirname(filepath_out)
        Log.logfile_write(log_dir, f"started single ({filepath_in} -> {filepath_out})")

        code_blocks = extract_code_blocks(filepath_in)

        if len(code_blocks) == 0:
            Log.error("No code blocks found")
            Log.logfile_write_extraction(
                log_dir, filepath_in, False, "no code blocks found"
            )
        elif len(code_blocks) == 1:
            Log.info("Found code block")
            with open(filepath_out, "w") as f:
                f.write(code_blocks[0].code)
            Log.logfile_write_extraction(log_dir, filepath_in, True, "")
        else:
            Log.info("Found multiple code blocks, chose the last")
            with open(filepath_out, "w") as f:
                f.write(code_blocks[-1].code)
            Log.logfile_write_extraction(
                log_dir, filepath_in, True, "found multiple code blocks, chose last"
            )

        Log.logfile_write(log_dir, "ended")

    @staticmethod
    def multiple(directory_in: str, directory_out: str):
        Log.logfile_write(
            directory_out, f"started multiple ({directory_in} -> {directory_out})"
        )
        for file in os.scandir(directory_in):
            if not file.is_file():
                continue

            code_blocks = extract_code_blocks(file.path)

            if len(code_blocks) == 0:
                Log.error(f"No code blocks found in '{file.name}'")
                Log.logfile_write_extraction(
                    directory_out, file.name, False, "no code blocks found"
                )
                continue

            outpath = os.path.join(
                directory_out,
                f"{file.name}.{code_blocks[0].language if code_blocks[0].language != '' else 'c'}",
            )

            if len(code_blocks) == 1:
                if os.path.exists(outpath):
                    Log.error(
                        f"One code block found, but the output file '{outpath}' already exists"
                    )
                    Log.logfile_write_extraction(
                        directory_out,
                        file.name,
                        False,
                        f"output file '{outpath}' already exists",
                    )
                    continue
                Log.info(f"Found code block in '{file.name}'")
                with open(outpath, "w") as f:
                    f.write(code_blocks[0].code)
                Log.logfile_write_extraction(directory_out, file.name, True, "")
            else:
                if os.path.exists(outpath):
                    Log.error(
                        f"Multiple code blocks found, but the output file '{outpath}' already exists"
                    )
                    Log.logfile_write_extraction(
                        directory_out,
                        file.name,
                        False,
                        f"output file '{outpath}' already exists",
                    )
                    continue
                Log.info(f"Found multiple code blocks in '{file.name}', chose the last")
                with open(outpath, "w") as f:
                    f.write(code_blocks[-1].code)
                Log.logfile_write_extraction(
                    directory_out,
                    file.name,
                    True,
                    "found multiple code blocks, chose last",
                )

        Log.logfile_write(directory_out, "ended")

    @staticmethod
    def __shutdown(signum, frame):
        sys.exit(0)
