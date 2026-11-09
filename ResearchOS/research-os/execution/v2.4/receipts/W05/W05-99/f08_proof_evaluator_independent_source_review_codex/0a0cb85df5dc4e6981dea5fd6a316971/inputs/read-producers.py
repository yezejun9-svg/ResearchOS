from pathlib import Path
import hashlib,json
ROOT=Path('D:/作品集/ResearchOS/research-os')
OUT=Path(__file__).resolve().parent
names=['runtime.go','runtime_coordinator_windows.go','resources.go','resources_recovery.go','runtime_permissions.go']
rows=[]
for name in names:
 p=ROOT/'internal/domain'/name
 raw=p.read_bytes()
 snapshot=OUT/'snapshots'/('extra-'+name)
 with snapshot.open('xb') as f:f.write(raw)
 rows.append({'original':{'path':p.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)},'snapshot':{'path':snapshot.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}})
with (OUT/'additional-inputs.before.json').open('x',encoding='utf-8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
for row in rows:
 p=Path(row['snapshot']['path']); lines=p.read_text(encoding='utf-8').splitlines()
 indexes=set()
 for i,line in enumerate(lines):
  if any(word in line for word in ['func ','identity[','resource_effects','SESSION_REBUILT','INSERT INTO resource_route_history']):
   for j in range(max(0,i-1),min(len(lines),i+7)):indexes.add(j)
 print('\nFILE '+p.name)
 for i in sorted(indexes):print(str(i+1)+': '+lines[i])
