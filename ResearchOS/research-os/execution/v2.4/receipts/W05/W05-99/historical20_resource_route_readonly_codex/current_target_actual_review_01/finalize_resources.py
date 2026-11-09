import sys
sys.dont_write_bytecode=True
import json,hashlib,types,subprocess
from pathlib import Path
O=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def read(p):return json.loads(Path(p).read_bytes())
def save(n,o):
 with (O/n).open('xb') as f:f.write((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
refs=[]
for entry in read(O/'current-source.pins.json')+read(O/'supplemental-source.pins.json'):
 if 'original' in entry:
  assert pin(entry['original']['path'])==entry['original'];refs.append(entry['original'])
resources=read(O/'go-dependency-resource-presence.json');expanded=[]
for e in resources['modules']:
 escaped=''.join('!'+c.lower() if c.isupper() else c for c in e['module']);p=R/'.local/gopath/pkg/mod'/(escaped+'@'+e['version']);expanded.append({'module':e['module'],'version':e['version'],'expanded_module_path':str(p),'expanded_module_present':p.is_dir(),'expanded_go_mod':pin(p/'go.mod') if (p/'go.mod').is_file() else None,'zip_present':e['.zip']['present']})
 refs.extend(e[k]['pin'] for k in ('.mod','.ziphash','.zip') if 'pin' in e[k])
refs.append(resources['go_tool']);refs.append(pin(R/'execution/project_identity.json'))
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';code=gp.read_bytes();assert hashlib.sha256(code).hexdigest()=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
refs.append(pin(gp));refs=list({x['path'].casefold():x for x in refs}.values())
m=types.ModuleType('route_read_guard');m.__file__=str(gp);exec(compile(code,str(gp),'exec'),m.__dict__)
g=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(refs)
try:
 for ref in refs:assert pin(ref['path'])==ref
 save('expanded-module-resource-presence.json',{'modules':expanded,'all_expanded_present':all(x['expanded_module_present'] for x in expanded),'module_content_not_compile_verified':True})
 save('source-and-resource-guard.refs.json',refs)
 evidence=[]
 anchors={
 'historical-source/apps/control/main.go':[(35,43),(61,105),(122,132)],
 'historical-source/apps/cli/main.go':[(39,53)],
 'historical-source/ops/backup/main.go':[(27,42),(75,84),(114,139),(148,167)],
 'historical-source/internal/domain/store.go':[(39,83)],
 'historical-source/internal/domain/backup.go':[(493,501),(513,531),(620,645)],
 'historical-source/internal/domain/client_session_fence.go':[(13,30)],
 'current-source/internal/domain/backup_migration.go':[(15,56),(96,150)],
 'current-source/internal/domain/backup_upgrade.go':[(21,23),(57,71),(245,271)],
 'current-source/internal/domain/backup_queue_upgrade.go':[(20,22),(320,330)],
 'current-source/internal/domain/backup_configuration_upgrade.go':[(15,22),(174,184)],
 'current-source/internal/domain/backup_prepared_abandonment_upgrade.go':[(26,28),(80,105),(561,589)],
 'current-source/internal/recoveryauthority/migration.go':[(11,14),(51,86)],
 'current-source/ops/supervisor/recovery_root/main_windows.go':[(23,50)],
 'current-source/apps/control/prepared_recovery_windows.go':[(21,36),(112,146)],
 'packet-evidence/LEG2-legacy_migration_fixture_test.go':[(99,114),(117,140)]}
 for path,ranges in anchors.items():
  p=O/path;lines=p.read_text(encoding='utf-8').splitlines()
  for lo,hi in ranges:evidence.append({'source_ref':pin(p),'line_start':lo,'line_end':min(hi,len(lines)),'text':'\n'.join(f'{i}: {lines[i-1]}' for i in range(lo,min(hi,len(lines))+1))})
 save('source-excerpts.json',evidence)
finally:save('sourceguard.close.json',g.close())
p=subprocess.run(['git','-C',str(R),'rev-parse','HEAD'],stdout=subprocess.PIPE,stderr=subprocess.PIPE);assert p.returncode==0 and p.stdout.decode().strip()=='adc460c2138528f163f7fdab5e8d81dde157b7fb'
save('final-identity-head-check.json',{'argv':['git','-C',str(R),'rev-parse','HEAD'],'actual_exit':p.returncode,'stdout':p.stdout.decode(),'stderr':p.stderr.decode(),'identity':pin(R/'execution/project_identity.json'),'identity_unchanged':pin(R/'execution/project_identity.json')==read(O/'resource-inventory.json')['identity']})
print(json.dumps({'all_expanded_modules_present':all(x['expanded_module_present'] for x in expanded),'missing_expanded_modules':[x['module'] for x in expanded if not x['expanded_module_present']],'guarded_refs':len(refs),'source_guard_closed':True,'source_excerpts':len(evidence),'product_execution':False},ensure_ascii=False))
