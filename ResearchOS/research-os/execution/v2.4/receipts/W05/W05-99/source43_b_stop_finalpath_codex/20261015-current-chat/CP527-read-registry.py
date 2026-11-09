import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')
wt = pathlib.Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\source43-b-stop-finalpath-20261015')
specs = [
    ('internal/host/roots.go', 1, 145),
    ('internal/host/backup_integration_windows_test.go', 1, 180),
    ('internal/host/host.go', 185, 240),
]
for name, start, end in specs:
    lines = (wt / name).read_text(encoding='utf-8').splitlines()
    print('===', name, '===')
    print('\n'.join(f'{n}: {lines[n-1]}' for n in range(start, min(end, len(lines)) + 1)))
