import os, re, subprocess, sys
from commands import COMMANDS
from utils import check_dir_exists

# Path to the root directory where main.py lives
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def color(str):
    return f"\033[33m{str}\033[0m"

while True:
    try:
        absolute_dir = os.getcwd()

        # Check if the current directory is inside or at the ROOT_DIR
        if absolute_dir == ROOT_DIR:
            current_dir = "minishell"
        elif absolute_dir.startswith(ROOT_DIR + os.sep):
            # Compute relative path inside project (e.g., 'test' or 'test/sub')
            rel_path = os.path.relpath(absolute_dir, ROOT_DIR)
            # Standardize path separators to standard slashes '/'
            rel_path = rel_path.replace("/", "\\")
            current_dir = f"minishell/{rel_path}"
        else:
            # Fallback for when you cd outside the project folder entirely
            current_dir = absolute_dir.split('\\')[-1] or absolute_dir

        prompt = "-- " + color(current_dir) + " > "
        user_input = input(f"{prompt}")

        user_input_stripped = user_input.strip()
        if not user_input_stripped:
            continue

        orig_stdin = sys.stdin
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        file_handles = []
        tokens = user_input_stripped.split()

        stdin_file = None
        stdout_file = None
        stdout_mode = 'w'  # Default mode for stdout redirection
        stderr_file = None
        stderr_mode = 'w'  # Default mode for stderr redirection
        stderr_to_stdout = False

        clean_tokens = []
        i = 0
        syntax_error = False

        while i < len(tokens):
            token = tokens[i]

            if token == '<':
                if i + 1 < len(tokens):
                    stdin_file = tokens[i + 1]
                    i += 2
                else:
                    print("Syntax error: No input file specified for redirection.")
                    syntax_error = True
                    break
            elif token == '>':
                if i + 1 < len(tokens):
                    stdout_file = tokens[i + 1]
                    stdout_mode = 'w'
                    i += 2
                else:
                    print("Syntax error: No output file specified for redirection.")
                    syntax_error = True
                    break
            elif token == '>>':
                if i + 1 < len(tokens):
                    stdout_file = tokens[i + 1]
                    stdout_mode = 'a'
                    i += 2
                else:
                    print("Syntax error: No output file specified for redirection.")
                    syntax_error = True
                    break
            elif token == '2>':
                if i + 1 < len(tokens):
                    stderr_file = tokens[i + 1]
                    stderr_mode = 'w'
                    i += 2
                else:
                    print("Syntax error: No error file specified for redirection.")
                    syntax_error = True
                    break
            elif token == '2>>':
                if i + 1 < len(tokens):
                    stderr_file = tokens[i + 1]
                    stderr_mode = 'a'
                    i += 2
                else:
                    print("Syntax error: No error file specified for redirection.")
                    syntax_error = True
                    break
            elif token == '2>&1':
                stderr_to_stdout = True
                i += 1
            else:
                clean_tokens.append(token)
                i += 1

        if syntax_error or not clean_tokens:
            if syntax_error:
                print("Syntax error in command.")
            continue

        command = clean_tokens[0]
        args = clean_tokens[1:]

        try:
            if stdin_file:
                sys.stdin = open(stdin_file, 'r')
                file_handles.append(sys.stdin)
            if stdout_file:
                sys.stdout = open(stdout_file, stdout_mode)
                file_handles.append(sys.stdout)
            if stderr_file:
                sys.stderr = open(stderr_file, stderr_mode)
                file_handles.append(sys.stderr)
            elif stderr_to_stdout:
                sys.stderr = sys.stdout

            if command in COMMANDS:
                try:
                    result = COMMANDS[command](args)
                    if result:
                        for line in result.splitlines():
                            print(f"  {line}")
                except Exception as e:
                    print(f"Error executing command: {e}")
            else:
                os.system(user_input_stripped)
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            for fh in file_handles:
                fh.close()

    except KeyboardInterrupt:
        print("\nExiting...")
        break