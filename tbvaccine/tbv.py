import os
import sys
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
    TB_END_RE = re.compile(r'^(?P<exception>[\w\.]+)\: (?P<description>.*?)$')
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
        """
        Decide whether the file in the traceback is one in our code_dir or not.
        """
        return self._file.startswith(self._code_dir) or \
               not self._file.startswith("/")

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
            self._print(line.rstrip("\r\n"))

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

    def process_line(self, line):
        """
        Process a line of input.
        """
        sl = line.rstrip("\r\n")
        if not sl:
            return ""

        if self._state == State.no_idea and sl == "Traceback (most recent call last):":
            # The first line of the traceback.
            self._state = State.in_traceback
            self._print(sl, "blue")
        elif self._state == State.in_traceback and self.TB_END_RE.match(sl):
            # The last line of the traceback.
            self._state = State.no_idea
            matches = self.TB_END_RE.match(sl).groupdict()
            self._print(matches["exception"], "red", "bright")
            self._print(": ")
            self._print(matches["description"], "green")
        elif self._state == State.in_traceback and self.TB_FILE_RE.match(line):
            # A file line.
            self._process_file_line(sl)
        elif self._state == State.in_traceback and sl.startswith("    "):
            # A code line.
            self._process_code_line(sl)
        else:
            self._print(sl)

        self._print("\n")

        output = self._buffer
        self._buffer = ""
        return output

    def format_tb(self, tb):
        """
        Format an entire traceback with ANSI colors.
        """
        return "".join(self.process_line(line) for line in tb.split("\n"))

    def print_exception(self, etype, value, tb):
        """
        Format and colorize a stack trace and the exception information.
        """
        tb_text = "".join(traceback.format_exception(etype, value, tb))
        formatted = self.format_tb(tb_text)
        sys.stderr.write(formatted)

    def format_exc(self):
        """
        Format the latest exception's traceback.
        """
        return self.format_tb(traceback.format_exc())


def add_hook():
    if not getattr(sys.stderr, 'isatty', lambda: False)():
        sys.stderr.write("\n\nNot an interactive session, "
                         "TBVaccine won't pretty print exceptions.\n\n")
        return
    tbv = TBVaccine()
    sys.excepthook = tbv.print_exception
