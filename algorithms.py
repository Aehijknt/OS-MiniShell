"""Six course scheduling algorithms; all implemented without algorithm packages.

Policies chosen where the assignment is underspecified:
- SJN and Priority are non-preemptive. Lower priority number = higher priority.
- MLQ: priority 0-3 high (RR q=2), 4-6 medium (RR q=4), >=7 low (FCFS).
  Higher queues preempt lower queues; interrupted jobs resume their remaining turn.
- MLFQ: 3 RR queues with quanta 2, 4, 8. All enter top queue, a used-up
  quantum demotes a job, and top queues preempt lower queues. No aging/boost.
- Context-switch overhead is zero; ties use input order.
"""
from collections import deque
from pcb import PCB


def schedule(source, algorithm, quantum=4):
    if algorithm not in ('fcfs', 'sjn', 'priority', 'rr', 'mlq', 'mlfq'):
        raise ValueError('Algorithm must be fcfs, sjn, priority, rr, mlq, or mlfq.')
    if type(quantum) is not int or quantum <= 0:
        raise ValueError('Quantum must be a positive integer.')
    jobs = [PCB(p.pid, p.arrival, p.burst, p.priority) for p in source]
    if not jobs:
        return jobs, []
    if algorithm in ('fcfs', 'sjn', 'priority'):
        return _nonpreemptive(jobs, algorithm)
    if algorithm == 'rr':
        return _rr(jobs, quantum)
    return _multilevel(jobs, algorithm)


def _append(timeline, pid, start, finish):
    if finish <= start:
        return
    if timeline and timeline[-1][0] == pid and timeline[-1][2] == start:
        last = timeline[-1]
        timeline[-1] = (pid, last[1], finish)
    else:
        timeline.append((pid, start, finish))


def _nonpreemptive(jobs, method):
    t, pending, timeline = 0, set(range(len(jobs))), []
    while pending:
        available = [i for i in pending if jobs[i].arrival <= t]
        if not available:
            next_time = min(jobs[i].arrival for i in pending)
            _append(timeline, 'IDLE', t, next_time)
            t = next_time
            continue
        if method == 'fcfs':
            i = min(available, key=lambda j: (jobs[j].arrival, j))
        elif method == 'sjn':
            i = min(available, key=lambda j: (jobs[j].burst, jobs[j].arrival, j))
        else:
            i = min(available, key=lambda j: (jobs[j].priority, jobs[j].arrival, j))
        p = jobs[i]
        p.state = 'Running'
        _append(timeline, p.pid, t, t + p.burst)
        t += p.burst
        p.remaining = 0
        p.completion = t
        p.state = 'Terminated'
        pending.remove(i)
    return jobs, timeline


def _rr(jobs, quantum):
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i].arrival, i))
    incoming, ready, t, done, timeline = 0, deque(), 0, 0, []
    while done < len(jobs):
        while incoming < len(order) and jobs[order[incoming]].arrival <= t:
            i = order[incoming]
            jobs[i].state = 'Ready'
            ready.append(i)
            incoming += 1
        if not ready:
            next_t = jobs[order[incoming]].arrival
            _append(timeline, 'IDLE', t, next_t)
            t = next_t
            continue
        i = ready.popleft()
        p = jobs[i]
        p.state = 'Running'
        duration = min(quantum, p.remaining)
        _append(timeline, p.pid, t, t + duration)
        t += duration
        p.remaining -= duration
        while incoming < len(order) and jobs[order[incoming]].arrival <= t:
            j = order[incoming]
            jobs[j].state = 'Ready'
            ready.append(j)
            incoming += 1
        if p.remaining:
            p.state = 'Ready'
            ready.append(i)
        else:
            p.completion = t
            p.state = 'Terminated'
            done += 1
    return jobs, timeline


def _multilevel(jobs, method):
    order = sorted(range(len(jobs)), key=lambda i: (jobs[i].arrival, i))
    queues = [deque(), deque(), deque()]
    levels = [0 if method == 'mlfq' else (0 if p.priority <= 3 else 1 if p.priority <= 6 else 2) for p in jobs]
    budget = [2 if method == 'mlfq' else (2 if levels[i] == 0 else 4 if levels[i] == 1 else 10**12) for i in range(len(jobs))]
    incoming, done, t, current, timeline = 0, 0, 0, None, []
    while done < len(jobs):
        while incoming < len(order) and jobs[order[incoming]].arrival <= t:
            j = order[incoming]
            jobs[j].state = 'Ready'
            queues[levels[j]].append(j)
            incoming += 1
        high_ready = next((level for level, q in enumerate(queues) if q), None)
        if current is not None and high_ready is not None and high_ready < levels[current]:
            jobs[current].state = 'Ready'
            queues[levels[current]].appendleft(current)
            current = None
        if current is None:
            if high_ready is None:
                next_t = jobs[order[incoming]].arrival
                _append(timeline, 'IDLE', t, next_t)
                t = next_t
                continue
            current = queues[high_ready].popleft()
            jobs[current].state = 'Running'
        p = jobs[current]
        _append(timeline, p.pid, t, t + 1)
        p.remaining -= 1
        budget[current] -= 1
        t += 1
        if p.remaining == 0:
            p.completion = t
            p.state = 'Terminated'
            done += 1
            current = None
        elif budget[current] == 0:
            if method == 'mlfq':
                levels[current] = min(2, levels[current] + 1)
                budget[current] = (2, 4, 8)[levels[current]]
            else:
                budget[current] = (2, 4, 10**12)[levels[current]]
            p.state = 'Ready'
            queues[levels[current]].append(current)
            current = None
    return jobs, timeline
