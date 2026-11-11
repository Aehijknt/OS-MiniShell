"""Multiple-instance deadlock detection based on Allocation, Request and Available.
Request is the outstanding *current* request, NOT the Max/Need matrix.
"""

def detect(system):
    if 'request' not in system:
        raise ValueError('Detection requires a "request" matrix in the input file.')
    work = system['available'][:]
    allocation = system['allocation']
    requests = system['request']
    finish = [not any(row) for row in allocation]
    changed = True
    while changed:
        changed = False
        for i in range(len(finish)):
            if not finish[i] and all(req <= avail for req, avail in zip(requests[i], work)):
                work = [avail + held for avail, held in zip(work, allocation[i])]
                finish[i] = True
                changed = True
    return [pid for i, pid in enumerate(system['processes']) if not finish[i]]
