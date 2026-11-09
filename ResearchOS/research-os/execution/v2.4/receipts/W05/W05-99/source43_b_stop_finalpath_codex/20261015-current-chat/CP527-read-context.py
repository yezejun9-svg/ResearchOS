import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

repo = pathlib.Path(r'D:\作品集\ResearchOS\research-os')
wt = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\source43-b-stop-finalpath-20261015')
items = [
    repo / 'execution/v2.4/receipts/W05/W05-99/host_stored_finalpath_diagnosis_codex/20261015-current-chat/diagnosis.json',
    repo / 'execution/v2.4/receipts/W05/W05-99/host_stored_finalpath_diagnosis_codex/20261015-current-chat/DIAGNOSIS.md',
    wt / 'internal/host/roots_windows.go',
]
for path in items:
    print('===', path, '===')
    print(path.read_text(encoding='utf-8'))
print('EXISTING_ROOTS_TEST', (wt / 'internal/host/roots_windows_test.go').exists())
