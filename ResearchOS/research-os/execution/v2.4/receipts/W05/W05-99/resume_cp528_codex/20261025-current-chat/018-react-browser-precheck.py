import json
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");W=R/'.local/worktrees/react-workbench-redesign-20261025'
for name in ['tests/ui/frontend-redesign-fixture.cjs','apps/web/src/components/app-shell.jsx']:
 p=W/name;lines=p.read_text(encoding='utf8').splitlines();print('FILE '+name+' lines='+str(len(lines)));print(chr(10).join(str(i)+': '+x for i,x in enumerate(lines,1)))
