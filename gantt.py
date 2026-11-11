"""Pretty-print scheduler results."""

def render(jobs, timeline, algorithm):
    lines = [f'ALGORITHM: {algorithm.upper()}', '', 'GANTT CHART']
    if timeline:
        lines.append(' '.join(f'| {pid} [{start}-{end}]' for pid, start, end in timeline) + ' |')
    else:
        lines.append('(empty queue)')
    lines += ['', f'{"PID":<10}{"State":<13}{"Arrival":>8}{"Burst":>8}{"Priority":>10}{"Completion":>12}{"Waiting":>10}{"Turnaround":>13}']
    wt, tat = 0, 0
    for p in jobs:
        turnaround = p.completion - p.arrival
        waiting = turnaround - p.burst
        wt += waiting
        tat += turnaround
        lines.append(f'{p.pid:<10}{p.state:<13}{p.arrival:>8}{p.burst:>8}{p.priority:>10}{p.completion:>12}{waiting:>10}{turnaround:>13}')
    n = len(jobs)
    lines.extend(['', f'Average waiting time: {wt/n if n else 0:.2f}', f'Average turnaround time: {tat/n if n else 0:.2f}'])
    return '\n'.join(lines)
