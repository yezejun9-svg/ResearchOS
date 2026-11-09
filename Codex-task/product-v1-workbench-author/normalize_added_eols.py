from pathlib import Path
from difflib import SequenceMatcher

root = Path(__file__).resolve().parent
relative = Path('apps/web/src/workbench.jsx')
baseline = (root / 'baseline' / relative).read_bytes().splitlines(keepends=True)
target = root / 'candidate' / relative
before = target.read_bytes()
current = before.splitlines(keepends=True)
result = []
for operation, i, j, a, b in SequenceMatcher(a=baseline, b=current, autojunk=False).get_opcodes():
    result.extend(current[a:b] if operation == 'equal' else [line.replace(b'\r\n', b'\n') for line in current[a:b]])
after = b''.join(result)
assert before.replace(b'\r\n', b'\n') == after.replace(b'\r\n', b'\n')
target.write_bytes(after)
print('ONLY_ADDED_EOL_NORMALIZED')
