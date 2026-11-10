from io import StringIO
import os, re, subprocess, sys
from commands import COMMANDS, ENV_VARS, expand_variables
from utils import check_dir_exists

# Path to the root directory where main.py lives
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

def color(str):
    return f"\033[33m{str}\033[0m"

def single_command(cmd_str, input_data=None):
    orig_stdin = sys.stdin
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    file_handles = []
    tokens = cmd_str.split()
    if not tokens:
        return ""

    if len(tokens) == 1 and "=" in tokens[0] and not tokens[0].startswith("=") and not tokens[0].endswith("="):
        key, value = tokens[0].split("=", 1)
        ENV_VARS[key] = value
        os.environ[key] = value
        return ""

    tokens = expand_variables(tokens)

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
        return ""

    command = clean_tokens[0]
    args = clean_tokens[1:]
    captured_output = ""

    try: 
        if stdin_file:
            f_in = open(stdin_file, 'r')
            file_handles.append(f_in)
            sys.stdin = f_in
        elif input_data is not None:
            sys.stdin = StringIO(input_data)

        if stdout_file:
            f_out = open(stdout_file, stdout_mode)
            file_handles.append(f_out)
            sys.stdout = f_out
        else:
            buffer = StringIO()
            sys.stdout = buffer

        if stderr_to_stdout:
            sys.stderr = sys.stdout
        elif stderr_file:
            f_err = open(stderr_file, stderr_mode)
            file_handles.append(f_err)
            sys.stderr = f_err

        if check_dir_exists(command):
            os.chdir(command)
        elif command in COMMANDS:
            result = COMMANDS[command](args)
            if result:
                print(result)
        else:
            os.system(" ".join(clean_tokens))

        if not stdout_file:
            captured_output = sys.stdout.getvalue()

    except Exception as e:
        print(f"Error executing command: {e}", file=orig_stderr)
    finally:
        sys.stdin = orig_stdin
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        for fh in file_handles:
            fh.close()

    return captured_output

def run_pipeline(user_input_str):
    pipe_segments = [seg.strip() for seg in user_input_str.split('|') if seg.strip()]
    if not pipe_segments:
        return

    previous_output = None

    for i, segment in enumerate(pipe_segments):
        previous_output = single_command(segment, input_data=previous_output)

    if previous_output:
        sys.stdout.write(previous_output)

while True:
    try:
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

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

        run_pipeline(user_input_stripped)

    except KeyboardInterrupt:
        print("\nExiting...")
        break