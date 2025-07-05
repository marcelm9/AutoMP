import os
import pathlib


def normalize_path(path: str, directory: str) -> str:
    if os.path.isabs(path):
        return path
    if path.startswith("~"):
        path = pathlib.Path(path).expanduser().as_posix()
    return os.path.abspath(os.path.join(directory, path))
