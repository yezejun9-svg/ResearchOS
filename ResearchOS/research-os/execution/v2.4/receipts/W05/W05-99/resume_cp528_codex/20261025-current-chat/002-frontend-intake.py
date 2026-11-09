from pathlib import Path
import subprocess,json,hashlib
R=Path(r'D:\作品集\ResearchOS\research-os')
for p in [Path(r'C:\Users\yqyyds\.agents\skills\frontend-ui-engineering\SKILL.md'),Path(r'C:\Users\yqyyds\.agents\skills\design-taste-frontend\SKILL.md')]:
 print('SKILL',str(p));print(p.read_text(encoding='utf-8-sig'))
r=subprocess.run(['rg','--files','-g','package.json','-g','AGENTS.md','-g','vite.config.*','-g','tsconfig*.json','-g','!execution/**','-g','!spec/**','-g','!node_modules/**','-g','!vendor/**'],cwd=R,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print('FRONTEND_INVENTORY_EXIT',r.returncode);print(r.stdout.decode('utf8','replace'));print(r.stderr.decode('utf8','replace'))
p=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/selector-verification.json'
if p.is_file():print('SELECTOR_PRIOR',p.read_text(encoding='utf-8-sig'))
