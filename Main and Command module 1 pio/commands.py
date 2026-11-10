import os
import sys
from typing import List
import platform
import shutil
import stat
import time
import re

class CommandError(Exception):
    """Raised by a command to signal failure. code = exit status (0 = success).
    An empty message means 'fail silently' (e.g. grep with no matches)."""
    def __init__(self, message="", code=1):
        super().__init__(message)
        self.message = message
        self.code = code

ENV_VARS = dict(os.environ)  # Initialize with current environment variables

def expand_variables(tokens):
    expanded_tokens = []
    for token in tokens:
        if token.startswith('$') and len(token) > 1:
            key = token[1:]
            value = ENV_VARS.get(key, "")
            expanded_tokens.append(value)
        else:
            expanded_tokens.append(token)
    return expanded_tokens

def env_command(args):
    lines = [f"{key}={value}" for key, value in ENV_VARS.items()]
    return "\n".join(lines)

def read_file(args):
    if not args:
        return sys.stdin.read().rstrip('\n')

    output = []
    for file_path in args:
        try: 
            with open(file_path, 'r') as f:
                output.append(f.read().rstrip('\n'))
        except Exception as e:
            print(f"cat: {file_path}: {e}", file=sys.stderr)
    return '\n'.join(output)

def grep_command(args):
    """grep [-i] [-n] [-v] PATTERN [FILE...]  (reads stdin if no file given)
    Exit status: 0 = match found, 1 = no match, 2 = error."""
    flags, rest = set(), []
    for a in args:
        if not rest and a.startswith('-') and len(a) > 1 and a[1:].isalpha():
            flags.update(a[1:])
        else:
            rest.append(a)

    bad = flags - set("inv")
    if bad:
        raise CommandError(f"grep: invalid option -- '{sorted(bad)[0]}'", 2)
    if not rest:
        raise CommandError("grep: usage: grep [-inv] PATTERN [FILE...]", 2)

    pattern, files = rest[0], rest[1:]
    try:
        rx = re.compile(pattern, re.IGNORECASE if 'i' in flags else 0)
    except re.error as e:
        raise CommandError(f"grep: invalid pattern '{pattern}': {e}", 2)

    sources, had_error = [], False
    if files:
        for fp in files:
            try:
                with open(fp, 'r') as f:
                    sources.append((fp, f.read().splitlines()))
            except FileNotFoundError:
                print(f"grep: {fp}: No such file or directory", file=sys.stderr)
                had_error = True
            except Exception as e:
                print(f"grep: {fp}: {e}", file=sys.stderr)
                had_error = True
    else:
        if sys.stdin.isatty():
            raise CommandError("grep: no input (give a file or pipe something in)", 2)
        sources.append((None, sys.stdin.read().splitlines()))

    out = []
    for name, lines in sources:
        for num, line in enumerate(lines, 1):
            hit = rx.search(line) is not None
            if hit != ('v' in flags):
                prefix = ""
                if len(files) > 1:
                    prefix += f"{name}:"
                if 'n' in flags:
                    prefix += f"{num}:"
                out.append(prefix + line)

    if not out:
        raise CommandError("", 2 if had_error else 1)
    return "\n".join(out)

def echo(args: List[str]) -> str:
    return " ".join(args) if args else ""

def list_directory(args: List[str]) -> str:
    long_format = "-l" in args
    paths = [a for a in args if a != "-l"]
    path = paths[0] if paths else "."
    try:
        entries = sorted(os.listdir(path))
        if long_format:
            lines = [ls_line(entry, os.path.join(path, entry)) for entry in entries]
            return "\n".join(lines)
        else:
            return "\n".join(entries)
    except FileNotFoundError:
        return f"Error: Directory '{path}' not found."
    except NotADirectoryError:
        return f"Error: '{path}' is not a directory."

def make_directory(args: List[str]) -> str:
    if not args:
        return "Error: No directory name provided."
    path = args[0]
    try:
        os.makedirs(path, exist_ok=True)
        return f"Directory '{path}' created successfully."
    except OSError as e:
        return f"Error: {str(e)}"

def change_directory(args: List[str]) -> str:
    if not args:
        return ""
    path = args[0]
    try:
        os.chdir(path)
        return ""
    except FileNotFoundError:
        return f"Error: Directory '{path}' not found."
    except NotADirectoryError:
        return f"Error: '{path}' is not a directory."

def present_working_directory(args: List[str]) -> str:
    try:
        return os.getcwd()
    except OSError as e:
        return f"Error: {str(e)}"

def remove_directory(args: List[str]) -> str:
    if not args:
        return "Error: No directory path provided."
    path = args[0]
    try:
        os.rmdir(path)
        return f"Directory '{path}' removed successfully."
    except FileNotFoundError:
        return f"Error: Directory '{path}' not found."
    except OSError as e:
        return f"Error: {str(e)}"

def touch_file(args: List[str]) -> str:
    if not args:
        return "Error: No file path provided."
    path = args[0]
    try:
        with open(path, 'a'):
            os.utime(path, None)
        return f"File '{path}' touched successfully."
    except OSError as e:
        return f"Error: {str(e)}"

def copy_file(args: List[str]) -> str:
    if len(args) < 2:
        return "Error: Source and destination paths required."
    src, dst = args[0], args[1]
    try:
        shutil.copy(src, dst)
        return f"Copied '{src}' to '{dst}'."
    except FileNotFoundError:
        return f"Error: File '{src}' not found."
    except OSError as e:
        return f"Error: {str(e)}"

def move_file(args: List[str]) -> str:
    if len(args) < 2:
        return "Error: Source and destination paths required."
    src, dst = args[0], args[1]
    try:
        shutil.move(src, dst)
        return f"Moved '{src}' to '{dst}'."
    except FileNotFoundError:
        return f"Error: '{src}' not found."
    except OSError as e:
        return f"Error: {str(e)}"

def remove_file(args: List[str]) -> str:
    if not args:
        return "Error: No file path provided."
    path = args[0]
    try:
        os.remove(path)
        return f"File '{path}' removed successfully."
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except IsADirectoryError:
        return f"Error: '{path}' is a directory."
    except OSError as e:
        return f"Error: {str(e)}"

def concatenate_file(args: List[str]) -> str:
    if not args:                      # `cat` with no args reads stdin (needed for pipes)
        return sys.stdin.read()
    out = []
    for path in args:
        try:
            with open(path, 'r') as f:
                out.append(f.read())
        except FileNotFoundError:
            raise CommandError(f"cat: {path}: No such file or directory")
        except IsADirectoryError:
            raise CommandError(f"cat: {path}: Is a directory")
        except Exception as e:
            raise CommandError(f"cat: {path}: {e}")
    return "".join(out)

def change_mode(args: List[str]) -> str:
    if len(args) < 2:
        return "Error: Mode and file path required."
    mode_str, path = args[0], args[1]
    try:
        mode = int(mode_str, 8)
        os.chmod(path, mode)
        return f"Permissions of '{path}' changed to '{mode_str}'."
    except ValueError:
        return f"Error: Invalid mode '{mode_str}'."
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except OSError as e:
        return f"Error: {str(e)}"

def ls_line(filename: str, filepath: str) -> str:
    st = os.stat(filepath)
    perm = stat.filemode(st.st_mode)
    size = st.st_size
    mtime = time.strftime('%b %d %H:%M', time.localtime(st.st_mtime))
    return f"{perm} {size:>8} {mtime} {filename}"

def get_system_info() -> str:
    info = [
        f"System: {platform.system()}",
        f"Node: {platform.node()}",
        f"Release: {platform.release()}",
        f"Version: {platform.version()}",
        f"Machine: {platform.machine()}",
        f"Processor: {platform.processor()}",
        f"Python: {platform.python_version()}"
    ]
    return "\n".join(info)

def help_command() -> str:
    commands = {
        "echo [args]": "Prints the provided arguments.",
        "ls [path]": "Lists the contents of the specified directory (default is current directory).",
        "mkdir [path]": "Creates a new directory at the specified path.",
        "cd [path]": "Changes the current working directory to the specified path.",
        "pwd": "Prints the current working directory path.",
        "rmdir [path]": "Removes an empty directory.",
        "touch [path]": "Creates an empty file or updates its modification time.",
        "cp [src] [dst]": "Copies a file from source to destination.",
        "mv [src] [dst]": "Moves/renames a file or directory.",
        "rm [path]": "Removes a file.",
        "cat [path]": "Displays the contents of a file.",
        "chmod [mode] [path]": "Changes the permissions of a file or directory.",
        "env": "Displays all environment variables.",
        "grep [pattern] [file]": "Searches for a pattern in a file.",
        "sysinfo": "Displays system information.",
        "help": "Displays this help message.",
        "exit": "Exits the command line interface."
    }

    help_text = "Available commands:\n"
    for cmd, desc in commands.items():
        help_text += f"  {cmd:<18} {desc}\n"

    return help_text.strip()

COMMANDS = {
    "echo": echo,
    "ls": list_directory,
    "mkdir": make_directory,
    "cd": change_directory,
    "pwd": present_working_directory,
    "rmdir": remove_directory,
    "touch": touch_file,
    "cp": copy_file,
    "mv": move_file,
    "rm": remove_file,
    "cat": concatenate_file,
    "chmod": change_mode,
    "env": env_command,
    "grep": grep_command,
    "sysinfo": lambda _: get_system_info(),
    "help": lambda _: help_command(),
    "exit": lambda _: exit()
}