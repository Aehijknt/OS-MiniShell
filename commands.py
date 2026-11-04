import os
from typing import List
import platform

def echo(args: List[str]) -> str:
    return " ".join(args) if args else ""

def list_directory(args: List[str]) -> str:
    path = args[0] if args else "."
    try:
        return "\n".join(os.listdir(path))
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
        "sysinfo": "Displays system information.",
        "help": "Displays this help message.",
        "exit": "Exits the command line interface."
    }

    help_text = "Available commands:\n"
    for cmd, desc in commands.items():
        help_text.append(f" {cmd<10} - {desc}")

    return "\n".join(help_text)

COMMANDS = {
    "echo": echo,
    "ls": list_directory,
    "mkdir": make_directory,
    "cd": change_directory,
    "sysinfo": lambda _: get_system_info(),
    "help": lambda _: help_command(),
    "exit": lambda _: exit()
}