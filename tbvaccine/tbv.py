import os
import sys
import traceback
import re
from enum import Enum

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import Terminal256Formatter as TerminalFormatter


#  term colour control codes
re_ansi_control_codes = re.compile(r'\x1b[^m]*m')


class State(Enum):
    no_idea = 0
    in_traceback = 1


class TBVaccine:
    TB_END_RE = re.compile(r'^(?P<exception>[\w\.]+)\: (?P<description>.*?)$')
    TB_FILE_RE = re.compile(r'^  File "(?P<filename>.*?)", line (?P<line>\d+), in (?P<func>.*)$')
    VAR_PREFIX = "|     "

    def __init__(self, code_dir=None, isolate=True, show_vars=True, max_length=79*4):
        # The directory we're interested in.
        if not code_dir:
            code_dir = os.getcwd()
        self._code_dir = code_dir

        # Whether to print interesting lines in color or not. If False,
        # all lines are printed in color.
        self._isolate = isolate

        # Our current state.
        self._state = State.no_idea

        # The filename of the line we're currently printing.
        self._file = None

        # The buffer that we use to build up the output in.
        self._buffer = ""

        # Whether to print variables for stack frames.
        self._show_vars = show_vars

        # Max length of printed variable lines
        self._max_length = max_length

    def _print(self, text, fg=None, style=None, max_length=None):
        if max_length and len(text) > max_length:
            # drop all ANSI control sequences
            text = re.sub(re_ansi_control_codes, "", text)
            if len(text) > max_length:
                text = text[:max_length] + " ... ({} more chars)".format(len(text) - max_length)
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

    def _process_var_line(self, line):
        """
        Process a line of variables in the traceback.
        """
        if self._show_vars is False or (self._isolate and not self._file_in_dir()):
            # Don't print.
            return False
        else:
            line = highlight(line, PythonLexer(), TerminalFormatter(style="monokai"))
            self._print(line.rstrip("\r\n"), max_length=self._max_length)
        return True

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
            base, fn = os.path.split(match["filename"])
            if base:
                self._print(base + os.sep, "cyan")
            self._print(fn, "cyan", style="bright")
            self._print("\", line ")
            self._print(match["line"], "yellow")
            self._print(", in ")
            self._print(match["func"], "magenta")

    def _process_line(self, line):
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
        elif self._state == State.in_traceback and sl.startswith(self.VAR_PREFIX):
            if not self._process_var_line(sl):
                return ""
        elif self._state == State.in_traceback and sl.startswith("    "):
            # A code line.
            self._process_code_line(sl)
        else:
            self._print(sl)

        self._print("\n")

        output = self._buffer
        self._buffer = ""
        return output

    def _format_tb_string_with_locals(self, etype, value, tb):
        """
        Return a traceback as a string, with the local variables in each stack.
        """
        original_tb = tb
        while 1:
            if not tb.tb_next:
                break
            tb = tb.tb_next

        stack = []
        f = tb.tb_frame
        while f:
            stack.append(f)
            f = f.f_back
        stack.reverse()

        lines = ["Traceback (most recent call last):\n"]
        for frame, line in zip(stack, traceback.format_tb(original_tb)):
            # Frame lines contain newlines, so we need to split on them.
            lines.extend(line.split("\n"))
            var_tuples = sorted(frame.f_locals.items())
            if not var_tuples:
                # There are no locals, so continue.
                continue

            max_length = max([len(x[0]) for x in var_tuples])
            for key, val in var_tuples:
                try:
                    val = str(val)
                except:
                    val = "<CANNOT CONVERT VALUE>"
                lines.append("%s%s = %s" % (self.VAR_PREFIX, key.ljust(max_length), val))
        lines.append("%s: %s" % (value.__class__.__name__, value))
        return "".join(self._process_line(line) for line in lines)

    def _format_tb_string(self, tb_string):
        """
        Format an entire traceback string with ANSI colors.
        """
        return "".join(self._process_line(line) for line in tb_string.split("\n"))

    def print_exception(self, etype, value, tb):
        """
        Format and colorize a stack trace and the exception information.
        """
        formatted = self._format_tb_string_with_locals(etype, value, tb)
        sys.stderr.write(formatted)

    def format_exc(self):
        """
        Format the latest exception's traceback.
        """
        return self._format_tb_string_with_locals(*sys.exc_info())


def add_hook(*args, **kwargs):
    if not getattr(sys.stderr, 'isatty', lambda: False)():
        sys.stderr.write("\n\nNot an interactive session, "
                         "TBVaccine won't pretty print exceptions.\n\n")
        return
    tbv = TBVaccine(*args, **kwargs)
    sys.excepthook = tbv.print_exception
