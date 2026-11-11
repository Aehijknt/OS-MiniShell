"""Banker's algorithm: safety test and provisional resource requests."""

def safety(system):
    work = system['available'][:]
    finish = [False] * len(system['processes'])
    order = []
    changed = True
    while changed:
        changed = False
        for i, pid in enumerate(system['processes']):
            if not finish[i] and all(need <= have for need, have in zip(system['need'][i], work)):
                work = [have + held for have, held in zip(work, system['allocation'][i])]
                finish[i] = True
                order.append(pid)
                changed = True
    return all(finish), order


def request(system, pid, counts):
    if pid not in system['processes']:
        raise ValueError(f'Unknown PID: {pid}')
    i = system['processes'].index(pid)
    if len(counts) != len(system['available']) or any(type(x) is not int or x < 0 for x in counts):
        raise ValueError('Request must contain nonnegative integer counts for every resource.')
    if any(x > n for x, n in zip(counts, system['need'][i])):
        return False, 'Request exceeds declared maximum remaining need.'
    if any(x > a for x, a in zip(counts, system['available'])):
        return False, 'Not enough resources available; process must wait.'
    # Provisional allocation. Original system is unchanged.
    clone = {
        'processes': system['processes'][:],
        'available': [a - x for a, x in zip(system['available'], counts)],
        'allocation': [row[:] for row in system['allocation']],
        'need': [row[:] for row in system['need']],
    }
    clone['allocation'][i] = [a + x for a, x in zip(clone['allocation'][i], counts)]
    clone['need'][i] = [n - x for n, x in zip(clone['need'][i], counts)]
    safe, sequence = safety(clone)
    return (True, 'GRANTED (safe sequence: ' + ' -> '.join(sequence) + ')') if safe else (False, 'DENIED: granting this request creates an unsafe state.')
