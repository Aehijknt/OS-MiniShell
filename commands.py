import os
from typing import List
import platform
import shutil
import stat
import time

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
    if not args:
        return "Error: No file path provided."
    path = args[0]
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File '{path}' not found."
    except IsADirectoryError:
        return f"Error: '{path}' is a directory."
    except OSError as e:
        return f"Error: {str(e)}"

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
    "sysinfo": lambda _: get_system_info(),
    "help": lambda _: help_command(),
    "exit": lambda _: exit()
}