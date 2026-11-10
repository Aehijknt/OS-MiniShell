from io import StringIO
import os, re, subprocess, sys
from commands import COMMANDS, ENV_VARS, expand_variables, CommandError

try:
    from utils import check_dir_exists
except ImportError:  # fallback if utils.py is missing
    def check_dir_exists(path):
        return os.path.isdir(path)

os.system("")  # enables ANSI colors in Windows cmd

# Path to the root directory where main.py lives
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Commands whose output is real data (never treated as an "Error..." message)
RAW_OUTPUT_COMMANDS = {"echo", "cat", "grep", "env", "sysinfo", "help"}


def color(str):
    return f"\033[33m{str}\033[0m"


def run_external(tokens):
    """Run a non-built-in program and capture its output. Returns exit status."""
    try:
        data = None if sys.stdin is sys.__stdin__ else sys.stdin.read()
        p = subprocess.run(tokens, input=data, capture_output=True, text=True)
    except FileNotFoundError:
        print(f"{tokens[0]}: command not found", file=sys.stderr)
        return 127
    except PermissionError:
        print(f"{tokens[0]}: permission denied", file=sys.stderr)
        return 126
    sys.stdout.write(p.stdout)
    sys.stderr.write(p.stderr)
    return p.returncode


def single_command(cmd_str, input_data=None):
    """Runs ONE command (no pipes/operators). Returns (captured_output, status)."""
    orig_stdin = sys.stdin
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    file_handles = []
    tokens = cmd_str.split()
    if not tokens:
        return "", 0

    # NAME=value assignment
    if len(tokens) == 1 and "=" in tokens[0] and not tokens[0].startswith("=") and not tokens[0].endswith("="):
        key, value = tokens[0].split("=", 1)
        ENV_VARS[key] = value
        os.environ[key] = value
        return "", 0

    tokens = expand_variables(tokens)

    stdin_file = None
    stdout_file = None
    stdout_mode = 'w'
    stderr_file = None
    stderr_mode = 'w'
    stderr_to_stdout = False

    clean_tokens = []
    i = 0
    syntax_error = False

    # (token, takes a filename, which variable it sets)
    while i < len(tokens):
        token = tokens[i]
        if token in ('<', '>', '>>', '2>', '2>>'):
            if i + 1 >= len(tokens):
                print(f"Syntax error: no file specified after '{token}'.", file=sys.stderr)
                syntax_error = True
                break
            target = tokens[i + 1]
            if token == '<':
                stdin_file = target
            elif token == '>':
                stdout_file, stdout_mode = target, 'w'
            elif token == '>>':
                stdout_file, stdout_mode = target, 'a'
            elif token == '2>':
                stderr_file, stderr_mode = target, 'w'
            elif token == '2>>':
                stderr_file, stderr_mode = target, 'a'
            i += 2
        elif token == '2>&1':
            stderr_to_stdout = True
            i += 1
        else:
            clean_tokens.append(token)
            i += 1

    if syntax_error:
        return "", 2
    if not clean_tokens:
        return "", 0

    command = clean_tokens[0]
    args = clean_tokens[1:]
    captured_output = ""
    status = 0

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
            sys.stdout = StringIO()

        if stderr_to_stdout:
            sys.stderr = sys.stdout
        elif stderr_file:
            f_err = open(stderr_file, stderr_mode)
            file_handles.append(f_err)
            sys.stderr = f_err

        if command in COMMANDS:
            try:
                result = COMMANDS[command](args)
            except CommandError as e:
                if e.message:
                    print(e.message, file=sys.stderr)
                status = e.code
            else:
                if result:
                    # Built-ins report errors as "Error: ..." strings -> send to stderr + fail
                    if command not in RAW_OUTPUT_COMMANDS and result.startswith("Error"):
                        print(result, file=sys.stderr)
                        status = 1
                    else:
                        print(result, end="" if result.endswith("\n") else "\n")
        elif check_dir_exists(command):
            os.chdir(command)
        else:
            status = run_external(clean_tokens)

        if not stdout_file:
            captured_output = sys.stdout.getvalue()

    except SystemExit:
        raise  # let `exit` work
    except FileNotFoundError as e:
        print(f"{e.filename}: No such file or directory", file=orig_stderr)
        status = 1
    except PermissionError as e:
        print(f"{e.filename}: Permission denied", file=orig_stderr)
        status = 1
    except Exception as e:
        print(f"Error executing command: {e}", file=orig_stderr)
        status = 1
    finally:
        sys.stdin = orig_stdin
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr
        for fh in file_handles:
            fh.close()

    return captured_output, status


def run_pipeline(user_input_str):
    """cmd1 | cmd2 | cmd3. Returns the exit status of the LAST command."""
    pipe_segments = [seg.strip() for seg in user_input_str.split('|') if seg.strip()]
    if not pipe_segments:
        return 0

    previous_output = None
    status = 0
    for segment in pipe_segments:
        previous_output, status = single_command(segment, input_data=previous_output)

    if previous_output:
        sys.stdout.write(previous_output)
    return status


def run_list(line):
    """Handles ;  &&  ||  between pipelines (evaluated left to right, like bash)."""
    parts = re.split(r'(&&|\|\||;)', line)
    status = run_pipeline(parts[0])

    for j in range(1, len(parts), 2):
        op, seg = parts[j], parts[j + 1]
        if not seg.strip():
            if op != ';':  # trailing ';' is fine, trailing && / || is not
                print(f"Syntax error: expected a command after '{op}'", file=sys.stderr)
                return 2
            continue
        if op == ';' or (op == '&&' and status == 0) or (op == '||' and status != 0):
            status = run_pipeline(seg)
    return status


IF_RE = re.compile(
    r'^if\s+(.+?)\s*;\s*then\s+(.+?)\s*(?:;\s*else\s+(.+?))?\s*;\s*fi$'
)


def execute(line):
    """Entry point for one line typed by the user."""
    if line == "if" or line.startswith("if "):
        m = IF_RE.match(line)
        if not m:
            print("Syntax error. Usage: if CMD; then CMD; [else CMD;] fi", file=sys.stderr)
            return 2
        cond, then_part, else_part = m.groups()
        if run_list(cond) == 0:
            return run_list(then_part)
        elif else_part:
            return run_list(else_part)
        return 0
    return run_list(line)


while True:
    try:
        sys.stdin = sys.__stdin__
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        absolute_dir = os.getcwd()

        if absolute_dir == ROOT_DIR:
            current_dir = "minishell"
        elif absolute_dir.startswith(ROOT_DIR + os.sep):
            rel_path = os.path.relpath(absolute_dir, ROOT_DIR)
            rel_path = rel_path.replace("/", "\\")
            current_dir = f"minishell/{rel_path}"
        else:
            current_dir = absolute_dir.split('\\')[-1] or absolute_dir

        prompt = "-- " + color(current_dir) + " > "
        user_input = input(f"{prompt}")

        user_input_stripped = user_input.strip()
        if not user_input_stripped:
            continue

        execute(user_input_stripped)

    except KeyboardInterrupt:
        print("\nExiting...")
        break
    except EOFError:  # Ctrl+D
        print("\nExiting...")
        break
    except Exception as e:  # last line of defense: the shell must never crash
        print(f"Error: {e}", file=sys.stderr)
