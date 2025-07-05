import os

from .log import Log


class Validator:
    @staticmethod
    def single(argv: list[str]) -> bool:
        if len(argv) < 4:
            Log.error(
                "Usage: python automp_extract.py single <filepath_in> <filepath_out>"
            )
            return False

        filepath_in = argv[2]
        filepath_out = argv[3]

        if not os.path.exists(filepath_in):
            Log.error(f"File '{filepath_in}' does not exist")
            return False
        if not os.path.isfile(filepath_in):
            Log.error(f"'{filepath_in}' is not a file")
            return False
        if os.path.exists(filepath_out):
            Log.error(f"File '{filepath_out}' already exists")
            return False
        return True

    @staticmethod
    def multiple(argv: list[str]) -> bool:
        if len(argv) < 4:
            Log.error(
                "Usage: python automp_extract.py multiple <directory_in> <directory_out>"
            )
            return False

        directory_in = argv[2]
        directory_out = argv[3]

        if not os.path.exists(directory_in):
            Log.error(f"Directory '{directory_in}' does not exist")
            return False
        if not os.path.isdir(directory_in):
            Log.error(f"'{directory_in}' is not a directory")
            return False
        if not os.path.exists(directory_out):
            Log.error(f"Directory '{directory_out}' does not exist")
            return False
        if not os.path.isdir(directory_out):
            Log.error(f"'{directory_out}' is not a directory")
            return False
        return True

    @staticmethod
    def watch(argv: list[str]) -> bool:
        if len(argv) < 4:
            Log.error(
                "Usage: python automp_extract.py watch <directory_in> <directory_out>"
            )
            return False

        return Validator.multiple(argv)
