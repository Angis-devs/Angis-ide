"""Lexer helpers for Angis source files."""

from __future__ import annotations

from dataclasses import dataclass
import shlex

from .errors import AngisSyntaxError


@dataclass(frozen=True)
class SourceLine:
    number: int
    text: str
    tokens: list[str]
    indent: int = 0


def strip_comment(line: str) -> str:
    """Strip comments while preserving # inside quoted strings."""
    in_quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char in {"'", '"'}:
            if in_quote == char:
                in_quote = None
            elif in_quote is None:
                in_quote = char
            continue
        if char == "#" and in_quote is None and (index + 1 >= len(line) or line[index + 1].isspace()):
            return line[:index]
    return line


def tokenize_line(line: str) -> list[str]:
    lexer = shlex.shlex(line, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.wordchars += ".+-*/="
    try:
        return list(lexer)
    except ValueError as exc:
        raise AngisSyntaxError(f"Could not tokenize line: {exc}") from exc


def lex(source: str) -> list[SourceLine]:
    lines: list[SourceLine] = []
    for number, raw_line in enumerate(source.splitlines(), start=1):
        without_comment = strip_comment(raw_line)
        text = without_comment.strip()
        if not text:
            continue
        indent = _indent_width(without_comment)
        lines.append(SourceLine(number=number, text=text, tokens=tokenize_line(text), indent=indent))
    return lines


def _indent_width(line: str) -> int:
    width = 0
    for char in line:
        if char == " ":
            width += 1
        elif char == "\t":
            width += 4
        else:
            break
    return width
