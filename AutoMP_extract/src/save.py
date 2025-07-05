import os

from .extract import CodeBlock


def save_codeblock_to_file(codeblock: CodeBlock, filepath_out: str) -> None:
    with open(filepath_out, "w") as f:
        f.write(codeblock.code)


def save_codeblock_to_directory(
    codeblock: CodeBlock, filepath_in: str, directory_out: str
) -> None:
    new_filename = ".".join(filepath_in.split(".")[:-1]) + f".{codeblock.language}"
    with open(os.path.join(directory_out, new_filename), "w") as f:
        f.write(codeblock.code)
