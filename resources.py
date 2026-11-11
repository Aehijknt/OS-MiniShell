"""Validate resource input. JSON inside .txt files for straightforward inspection."""
import json
from pathlib import Path


def load_system(filename):
    obj = json.loads(Path(filename).read_text(encoding='utf-8'))
    names = obj['processes']
    alloc = obj['allocation']
    maximum = obj['max']
    available = obj['available']
    if not isinstance(names, list) or len(set(names)) != len(names) or not names:
        raise ValueError('processes must contain unique process names.')
    m, n = len(available), len(names)
    if not m or len(alloc) != n or len(maximum) != n:
        raise ValueError('Invalid matrix dimensions.')
    matrices = [alloc, maximum]
    if 'request' in obj:
        matrices.append(obj['request'])
    if any(len(matrix) != n or any(len(row) != m for row in matrix) for matrix in matrices):
        raise ValueError('Each matrix must have one row per process and one column per resource.')
    if any(type(x) is not int or x < 0 for row in [available] + [r for mat in matrices for r in mat] for x in row):
        raise ValueError('Resource counts must be nonnegative integers.')
    if any(alloc[i][j] > maximum[i][j] for i in range(n) for j in range(m)):
        raise ValueError('Allocation cannot exceed maximum demand.')
    obj['need'] = [[maximum[i][j] - alloc[i][j] for j in range(m)] for i in range(n)]
    if 'request' in obj and any(obj['request'][i][j] > obj['need'][i][j] for i in range(n) for j in range(m)):
        raise ValueError('Outstanding request must not exceed remaining need.')
    return obj
