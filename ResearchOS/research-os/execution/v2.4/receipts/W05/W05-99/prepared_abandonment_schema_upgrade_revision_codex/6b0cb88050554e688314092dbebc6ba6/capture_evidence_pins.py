from pathlib import Path
import json,hashlib
root=Path(r'D:/作品集/ResearchOS/research-os')
own=Path("D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\prepared_abandonment_schema_upgrade_revision_codex\\6b0cb88050554e688314092dbebc6ba6")
run=root/'execution/v2.4/receipts/W05/W05-99/integration_codex/prepared-schema24-composition-root-3b35dff6a15e4e3e'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
pins=json.loads((own/'base-refs.json').read_text(encoding='utf-8'))
for name in ['validation.closed.json','failure-origin.768.json','historical-backup-regression.stdout.raw','historical-backup-regression.stderr.raw','historical-backup-regression.invocation.json']:
 pins.append(ref(run/name))
for name in ['internal/domain/client_protocol.go','internal/domain/client_protocol_sessions.go','internal/domain/durability.go']:
 pins.append(ref(root/name))
(own/'base-refs.json').write_text(json.dumps(pins,indent=2),encoding='utf-8')
lines=(run/'historical-backup-regression.stdout.raw').read_text(encoding='utf-8').splitlines()
failures=[]
for l in lines:
 try: x=json.loads(l)
 except ValueError: continue
 if x.get('Action')=='fail' and x.get('Test'):failures.append(x)
print(json.dumps({'failures':failures,'pins':len(pins),'guard_drift':[x for x in pins if ref(Path(x['path']))!=x]},indent=2))

