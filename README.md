# Shelldon OS (MiniShell + OS Simulators)

**Course:** CmpSc 123 — Operating Systems  
**Project:** Group Project: MiniShell + Simulated OS  

Shelldon OS is a custom Python command-line shell that implements core Bash functionality (built-in file utilities, Windows-compatible octal permissions, stream redirection, pipes, environment variables, conditional execution, system diagnostics, and regex pattern search) alongside integrated **CPU Process Scheduling** and **Deadlock Detection & Avoidance** simulators.

---

## Project Structure

```text
ShelldonOS/
├── main.py                  # Main shell loop, prompt rendering, and command router
├── commands.py              # Module 1 built-ins and Module 2/3 simulator bridges
├── algorithms.py            # Module 2: FCFS, SJN, Priority, RR, MLQ, and MLFQ logic
├── gantt.py                 # Module 2: Text Gantt chart and PCB table formatter
├── pcb.py                   # Module 2: Process Control Block dataclass & JSON loader
├── banker.py                # Module 3: Banker's safety check & provisional request logic
├── detection.py             # Module 3: Multi-instance deadlock detection algorithm
├── resources.py             # Module 3: System resource matrix validator & JSON loader
├── shelltest.py             # Automated subprocess test suite for shell verification
├── README.md                # Project documentation and usage guide
└── test/
    ├── scheduling/
    │   ├── processes.txt            # Main dataset for comparing all 6 scheduling algorithms
    │   ├── idle_gap.txt             # Edge case: staggered arrivals with CPU idle gaps
    │   └── edge_empty.txt           # Edge case: empty process queue
    └── deadlock/
        ├── safe_system.txt          # Safe system state for Banker's algorithm tests
        ├── deadlocked_system.txt    # Circular wait state for deadlock detection
        └── edge_zero_alloc.txt      # Edge case: processes holding zero allocated resources
```

---

## Requirements & Setup

* **Python Version:** Python 3.8 or higher
* **Dependencies:** Uses only Python's built-in standard library (`os`, `sys`, `json`, `re`, `shutil`, `stat`, `platform`, `time`, `subprocess`, `collections`, `dataclasses`, `pathlib`, `typing`). No external third-party packages are required.

### How to Launch

1. Open a terminal (Command Prompt, PowerShell, VS Code Terminal, or Bash) in the root project directory.
2. Start the interactive shell:
   ```bash
   python main.py
   ```
3. To run the automated test runner outside the shell:
   ```bash
   python shelltest.py
   ```

---

## Command Reference

### Module 1: Shell Core Built-ins

| Command | Syntax / Example | Description |
| :--- | :--- | :--- |
| `pwd` | `pwd` | Print the current working directory path. |
| `cd` | `cd <directory>` | Change the current working directory (`..` supported). |
| `ls` | `ls [path]` / `ls -l [path]` | List directory contents; `-l` displays Unix-style permissions, sizes, and timestamps. |
| `mkdir` | `mkdir <dir_name>` | Create a new directory (including parent directories if needed). |
| `rmdir` | `rmdir <dir_name>` | Remove an empty directory. |
| `touch` | `touch <file>` | Create an empty file or update its modification timestamp. |
| `cp` | `cp <src> <dest>` | Copy a file from source to destination. |
| `mv` | `mv <src> <dest>` | Move or rename a file or directory. |
| `rm` | `rm <file>` | Remove a file. |
| `cat` | `cat [file...]` | Output file contents to `stdout` (reads from `stdin` when piped). |
| `chmod` | `chmod <mode> <file>` | Update file permissions using numeric octal modes (e.g., `755`, `644`). |
| `echo` | `echo Hello $NAME` | Print arguments and expand shell variables (`$NAME`) to `stdout`. |
| `grep` | `grep [-inv] <pattern> [file...]` | Search lines matching a regex pattern (`-i` ignore case, `-n` line numbers, `-v` invert match). |
| `env` | `env` | Display all environment and assigned shell variables. |
| `NAME=val` | `USER=Shelldon` | Assign a shell variable in the current session. |
| `sysinfo` | `sysinfo` | Display host operating system, node, release, architecture, and Python version info. |
| `help` | `help` | Display the list of available built-in commands. |
| `exit` | `exit` | Exit Shelldon OS. |

#### Stream Redirection, Pipes, and Conditionals

* **Redirection:**
  * `cmd > file.txt` — Redirect `stdout` to a file (overwrite).
  * `cmd >> file.txt` — Redirect `stdout` to a file (append).
  * `cmd < file.txt` — Read `stdin` from a file.
  * `cmd 2> err.txt` — Redirect `stderr` to a file.
  * `cmd 2>&1` — Redirect `stderr` into `stdout`.
* **Pipes:**
  * `cmd1 | cmd2` — Pipe the `stdout` of `cmd1` into the `stdin` of `cmd2` (e.g., `ls | grep -i txt`).
* **Conditional Execution:**
  * `cmd1 ; cmd2` — Execute `cmd1` followed sequentially by `cmd2`.
  * `cmd1 && cmd2` — Execute `cmd2` only if `cmd1` succeeds (exit code `0`).
  * `cmd1 || cmd2` — Execute `cmd2` only if `cmd1` fails (non-zero exit code).
  * `if <cond> ; then <cmd1> ; else <cmd2> ; fi` — Conditional branching based on command exit status.

---

### Module 2: Process Scheduling Simulator (`sched`)

Simulates CPU scheduling algorithms from a JSON-formatted process list, printing a text Gantt chart, a full Process Control Block (PCB) table (`New`, `Ready`, `Running`, `Terminated`), and average waiting/turnaround times.

**Syntax:**
```bash
sched <fcfs|sjn|priority|rr|mlq|mlfq> [--quantum N] <processes_file>
```

**Supported Algorithms:**
* `fcfs` — First-Come, First-Served (non-preemptive)
* `sjn` — Shortest Job Next (non-preemptive)
* `priority` — Priority Scheduling (non-preemptive; lower number = higher priority)
* `rr` — Round-Robin (preemptive; defaults to `--quantum 4` if omitted)
* `mlq` — Multilevel Queue (Queue 0: priority `0–3` RR `q=2`; Queue 1: priority `4–6` RR `q=4`; Queue 2: priority `>=7` FCFS)
* `mlfq` — Multilevel Feedback Queue (3 preemptive RR queues with quanta `2`, `4`, and `8`)

**Example Commands:**
```bash
sched fcfs test/scheduling/processes.txt
sched sjn test/scheduling/processes.txt
sched priority test/scheduling/processes.txt
sched rr --quantum 4 test/scheduling/processes.txt
sched mlq test/scheduling/processes.txt
sched mlfq test/scheduling/processes.txt
```

**Edge Case Tests:**
```bash
sched fcfs test/scheduling/idle_gap.txt
sched rr test/scheduling/edge_empty.txt
```

---

### Module 3: Deadlock Simulator (`deadlock`)

Simulates multi-instance deadlock detection and Banker's deadlock avoidance from JSON-formatted resource state files.

**Syntax:**
```bash
deadlock detect <file>
deadlock banker <file> [--request <PID> <r1> <r2> ...]
```

**Example Commands:**
```bash
# Check if a system is in a safe state and print a safe execution sequence
deadlock banker test/deadlock/safe_system.txt

# Evaluate a provisional resource request (Granted)
deadlock banker test/deadlock/safe_system.txt --request P1 1 0 2

# Evaluate a provisional resource request (Denied — Unsafe State)
deadlock banker test/deadlock/safe_system.txt --request P0 0 2 0

# Detect deadlocked processes and output a victim process to terminate
deadlock detect test/deadlock/deadlocked_system.txt

# Edge case: zero allocated resources
deadlock detect test/deadlock/edge_zero_alloc.txt
```

---

## Input File Formats

### Scheduling Input (`test/scheduling/processes.txt`)
JSON array of process objects:
```json
[
  {"pid": "P1", "arrival": 0, "burst": 8, "priority": 2},
  {"pid": "P2", "arrival": 1, "burst": 4, "priority": 5}
]
```

### Deadlock Input (`test/deadlock/safe_system.txt`)
JSON object defining `processes`, `available` vector, `max` matrix, `allocation` matrix, and optional `request` matrix (required for `deadlock detect`):
```json
{
  "processes": ["P0", "P1", "P2"],
  "available": [3, 3, 2],
  "max": [[7, 5, 3], [3, 2, 2], [9, 0, 2]],
  "allocation": [[0, 1, 0], [2, 0, 0], [3, 0, 2]],
  "request": [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
}
```