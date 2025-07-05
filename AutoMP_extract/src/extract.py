from dataclasses import dataclass
import re


@dataclass
class CodeBlock:
    language: str
    code: str
    length: int


def extract_code_blocks(filepath) -> list[CodeBlock]:
    code_blocks = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"```(\w*)\n(.*?)\n```"
    matches = re.findall(pattern, content, re.DOTALL)

    for language, code in matches:
        code_blocks.append(CodeBlock(language, code, len(code)))

    return code_blocks
