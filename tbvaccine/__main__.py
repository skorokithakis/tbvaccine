import os
import sys
import tbvaccine

tbvaccine.add_hook()

# Check that a script was passed in.
if len(sys.argv) <= 1:
    raise SystemExit("Usage: python -m tbvaccine my_script.py")

# Check that the script exists.
script_path = sys.argv[1]
if not os.path.exists(script_path):
    raise SystemExit("Error: '%s' does not exist" % script_path)

# Replace tbvaccine's dir with script's dir in the module search path.
sys.path[0] = os.path.dirname(script_path)

# Remove tbvaccine from the arg list.
del sys.argv[0]

def initialize():
    if sys.platform.startswith('win32'):

        # Only windows requires this
        import ctypes

        # Winapi constants
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 4
        INVALID_HANDLE_VALUE = -1
        STD_OUTPUT_HANDLE = -11

        # Winapi functions
        GetStdHandle = ctypes.windll.kernel32.GetStdHandle
        GetConsoleMode = ctypes.windll.kernel32.GetConsoleMode
        SetConsoleMode = ctypes.windll.kernel32.SetConsoleMode

        console_mode = ctypes.c_int()

        # Get the stdout handle
        stdout_handle = GetStdHandle(STD_OUTPUT_HANDLE)
        if stdout_handle == INVALID_HANDLE_VALUE:
            return False

        # Get the console mode
        get_console_mode_ok = GetConsoleMode(stdout_handle, ctypes.byref(console_mode))
        if not get_console_mode_ok:
            return False

        # Change the console mode
        console_mode = console_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING

        # Set the new console mode
        set_console_mode_ok = SetConsoleMode(stdout_handle, console_mode)
        if not set_console_mode_ok:
            return False

    # Successful initialization
    return True

with open(script_path) as script_file:
    initialize()

    code = compile(script_file.read(), script_path, 'exec')
    variables = {
        '__name__': '__main__'
    }
    exec(code, variables, variables)

