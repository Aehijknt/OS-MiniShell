"""Process Control Blocks and input validation."""
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PCB:
    pid: str
    arrival: int
    burst: int
    priority: int
    state: str = 'New'
    remaining: int = 0
    completion: int = 0

    def __post_init__(self):
        self.remaining = self.burst


def load_processes(filename):
    data = json.loads(Path(filename).read_text(encoding='utf-8'))
    if not isinstance(data, list):
        raise ValueError('Process input must be a JSON list.')
    processes = []
    seen = set()
    for row in data:
        pid = str(row['pid'])
        if not pid or pid in seen:
            raise ValueError(f'Duplicate or empty PID: {pid!r}')
        seen.add(pid)
        arrival, burst, priority = (row[k] for k in ('arrival', 'burst', 'priority'))
        if any(type(v) is not int for v in (arrival, burst, priority)):
            raise ValueError(f'PID {pid}: arrival, burst, and priority must be integers.')
        if arrival < 0 or burst <= 0 or priority < 0:
            raise ValueError(f'PID {pid}: require arrival >= 0, burst > 0, priority >= 0.')
        processes.append(PCB(pid, arrival, burst, priority))
    return processes
