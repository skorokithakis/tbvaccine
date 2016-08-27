#!/usr/bin/env python3

import os
import traceback
import re
from enum import Enum

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter as TerminalFormatter


class State(Enum):
    no_idea = 0
    in_traceback = 1


class TBVaccine:
    TB_END_RE = re.compile(r'^(?P<exception>\w+)\: (?P<description>.*?)$')
    TB_FILE_RE = re.compile(r'^  File "(?P<filename>.*?)", line (?P<line>\d+), in (?P<func>.*)$')

    def __init__(self, code_dir=None, isolate=True):
        # The directory we're interested in.
        if not code_dir:
            code_dir = os.getcwd()
        self._code_dir = code_dir

        # Whether to print interesting lines in color or not.
        self._isolate = isolate

        # Our current state.
        self._state = State.no_idea

        # The filename of the line we're currently printing.
        self._file = None

        # The buffer that we use to build up the output in.
        self._buffer = ""

    def _print(self, text, fg=None, style=None):
        if fg or style:
            styles = {"bright": 1, None: 0}
            colors = {
                "black": 30,
                "red": 31,
                "green": 32,
                "yellow": 33,
                "blue": 34,
                "magenta": 35,
                "cyan": 36,
                "gray": 37,
            }
            text = "\x1b[%d;%dm%s\x1b[m" % (styles[style], colors[fg], text)
        self._buffer += text

    def _file_in_dir(self):
        return self._file.startswith(self._code_dir)

    def _process_code_line(self, line):
        """
        Process a line of code in the traceback.
        """
        if self._isolate and not self._file_in_dir():
            # Print without colors.
            self._print(line)
        else:
            if self._isolate:
                line = line[1:]
                self._print(">", fg="red", style="bright")
            line = highlight(line, PythonLexer(), TerminalFormatter(style="monokai"))
            self._print(line)

    def _process_file_line(self, line):
        """
        Process a "file" line of traceback.
        """
        match = self.TB_FILE_RE.match(line).groupdict()
        self._file = match["filename"]

        if self._isolate and not self._file_in_dir():
            # Print without colors.
            self._print(line)
        else:
            self._print("  File \"")
            self._print(match["filename"], "cyan")
            self._print("\", line ")
            self._print(match["line"], "yellow")
            self._print(", in ")
            self._print(match["func"], "magenta")
            self._print("\n")

    def process_line(self, line):
        """
        Process a line of input.
        """
        sl = line.strip()
        if self._state == State.no_idea and sl == "Traceback (most recent call last):":
            self._state = State.in_traceback
            self._print(line, "blue")
        elif self._state == State.in_traceback and self.TB_END_RE.match(sl):
            self._state = State.no_idea
            matches = self.TB_END_RE.match(sl).groupdict()
            self._print(matches["exception"], "red", "bright")
            self._print(": ")
            self._print(matches["description"], "green")
            self._print("\n")
        elif self._state == State.in_traceback and self.TB_FILE_RE.match(line):
            self._process_file_line(line)
        elif self._state == State.in_traceback and line.startswith("    "):
            self._process_code_line(line)
        else:
            self._print(line)

        output = self._buffer
        self._buffer = ""
        return output

    def format_tb(self, tb):
        """
        Format an entire traceback with ANSI colors.
        """
        return "\n".join(self.process_line(line) for line in tb.split("\n"))

    def format_exc(self):
        """
        Format the latest exception's traceback.
        """
        return self.format_tb(traceback.format_exc())
