import sys
sys.dont_write_bytecode = True
import hashlib
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
T5 = R / '.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2'
S = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')

CORE = {
    'internal/domain/runtime_sessions_windows.go': [(1, 163)],
    'internal/domain/client_protocol_sessions.go': [(125, 212), (294, 381)],
    'internal/domain/client_protocol_configuration.go': [(641, 824)],
    'internal/domain/client_protocol.go': [(875, 968)],
    'internal/domain/client_protocol_goal.go': [(1, 55), (270, 341)],
    'internal/domain/client_protocol_goal_test.go': [(1, 48), (272, 323)],
}

def emit(root, rel, ranges):
    path = root / rel
    raw = path.read_bytes()
    lines = raw.decode('utf-8').splitlines()
    print('FILE', path.as_posix(), 'SHA256', hashlib.sha256(raw).hexdigest(), 'BYTES', len(raw))
    for start, end in ranges:
        for number in range(start, min(end, len(lines)) + 1):
            print(str(number) + ': ' + lines[number - 1])

if sys.argv[1] == 'core':
    for rel, ranges in CORE.items():
        emit(T5, rel, ranges)
        main = (R / rel).read_bytes()
        candidate = (T5 / rel).read_bytes()
        print('MAIN_PIN', rel, hashlib.sha256(main).hexdigest(), len(main), 'SAME', main == candidate)
        if main != candidate:
            emit(R, rel, ranges)
elif sys.argv[1] == 'ranges':
    import json
    root = {'T5': T5, 'Main': R, 'Spec': S}[sys.argv[2]]
    ranges = json.loads(sys.argv[4])
    emit(root, sys.argv[3], ranges)
else:
    raise ValueError('unsupported read-only inspection mode')
