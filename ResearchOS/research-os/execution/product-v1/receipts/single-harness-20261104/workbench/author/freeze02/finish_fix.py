from pathlib import Path
from difflib import SequenceMatcher
import hashlib
import shutil

root = Path(__file__).resolve().parent
target = root / 'candidate/apps/web/src/workbench.jsx'
raw = target.read_bytes()
start, end = raw.index(b'function NativeHarnessWorkbench('), raw.index(b'function NativeMuWorkbench(')
block = raw[start:end]
for before, after in [
    (b'<ConversationWelcome setDraft={setDraft} composer={composer}/>', b'<ConversationWelcome setDraft={editDraft} composer={composer}/>'),
    (b'onChange={event => setDraft(event.target.value)}', b'onChange={event => editDraft(event.target.value)}'),
]:
    assert block.count(before) == 1
    block = block.replace(before, after)
raw = raw[:start] + block + raw[end:]
baseline = (root / 'baseline/apps/web/src/workbench.jsx').read_bytes().splitlines(keepends=True)
current = raw.splitlines(keepends=True)
lines = []
for operation, i, j, a, b in SequenceMatcher(a=baseline, b=current, autojunk=False).get_opcodes():
    lines.extend(current[a:b] if operation == 'equal' else [line.replace(b'\r\n', b'\n') for line in current[a:b]])
after = b''.join(lines)
assert raw.replace(b'\r\n', b'\n') == after.replace(b'\r\n', b'\n')
target.write_bytes(after)
qa = root.parent / 'product-v1-workbench-independent-qa-20261104/review01'
for name, expected in [
    ('review.json', '627c1c1977906aa94f058606f00bb24f58659133c5420643fce9253539783767'),
    ('EVIDENCE.json', '8163a866f52a4426424745176f4b3a8888df217bdcc32a7a2d34b3f199cb69de'),
]:
    source = qa / name
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected
    shutil.copyfile(source, root / 'prior-evidence' / name)
print('EDIT_VERSION_AND_VIEW_SCOPE_WIRED_OLD_QA_REPORTS_PINNED')
