import subprocess,sys
from pathlib import Path
N=Path(__file__).parent
text=(N/'verify_c51_preseal_r2.py').read_text(encoding='utf8')
old="f['name'].endswith('.native-exit.txt')"
assert text.count(old)==1
text=text.replace(old,"(f['name'].endswith('.native-exit.txt') or f['name'].endswith('.exit.txt'))")
for a,b in [('C51-root-patch-check-r2.','C51-root-patch-check-r3.'),('C51-DIAGNOSTIC-LEDGER.root-snapshot-89.jsonl','C51-DIAGNOSTIC-LEDGER.root-snapshot-89-r3.jsonl'),('C51-root-preseal-verification-r2.json','C51-root-preseal-verification-r3.json')]:text=text.replace(a,b)
p=N/'verify_c51_preseal_r3.py'
with p.open('x',encoding='utf8')as f:f.write(text)
raise SystemExit(subprocess.run([sys.executable,'-B','-X','utf8',str(p)]).returncode)

