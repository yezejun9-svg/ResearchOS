import datetime,hashlib,json,sys
from pathlib import Path
E=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def check(v):
 p=Path(v['path']);assert ref(p)['sha256']==v['sha256'] and p.stat().st_size==v['bytes'];return p
assert len(sys.argv)==2
sp=Path(sys.argv[1]).resolve();assert sp.parent==E/'controller'
s=load(sp);p=load(check(s['payload_ref']));f=load(check(s['fixture_public_ref']));r=load(E/'harness/rehearsal.public.json')
assert s['phase']=='grant' and s['case']=='wrong-purpose' and s['job_binding_id']==load(E/'controller/controller.started.json')['job_binding_id']
assert s['snapshot_guard_cleanup']['closed'] and not s['snapshot_guard_cleanup']['errors'] and all(x['matches'] for x in s['declared_pin_observations'])
assert set(p)=={'schema','purpose','release_sha256','nonce','issued_utc','expires_utc','root','root_identity','database','database_identity','tuple','pins'}
assert p['schema']=='researchos.recovery-grant.v1' and p['purpose']=='RESEARCHOS_PREPARED_HISTORICAL_ADOPTION_V1'
assert s['sign_kind']=='grant' and p['release_sha256']==sha((Path(s['signed_destination']).parent/'recovery-release.json').read_bytes()) and len(bytes.fromhex(p['nonce']))==32
now=datetime.datetime.now(datetime.timezone.utc);issued=datetime.datetime.fromisoformat(p['issued_utc']);expires=datetime.datetime.fromisoformat(p['expires_utc']);assert issued<=now<expires and 0<(expires-issued).total_seconds()<=240
assert p['root']==f['root'] and p['database']==f['database'] and p['root_identity']==s['measured_native_ids']['root'] and p['database_identity']==s['measured_native_ids']['database']
assert p['tuple']=={'project_id':'','task_id':'','run_id':'','runtime_id':'','owner_root':'','epoch':0,'run_revision':0,'task_revision':0,'dispatch_key':'','manifest_hash':''}
for pin in p['pins']:check(pin)
roles=[v['role'] for v in p['pins']];assert len(roles)==len(set(roles))
for role in ['target-rehearsal-program','handoff-binding','backup-producer-stdout','backup-producer-observation','source-program','target-program','migration-sql','encrypted-backup-manifest','isolated-restore-rehearsal']:assert role in roles
assert sum(x.startswith('source-inventory:') for x in roles)>0 and sum(x.startswith('target-inventory:') for x in roles)>0 and sum(x.startswith('encrypted-backup-payload:') for x in roles)>0
assert Path(s['signed_destination']).name=='current-schema24-to25-grant.json' and s['sign_kind']=='grant'
out={'schema':'researchos.root-native-concrete-grant-inspection/1','at':now.isoformat(),'snapshot_ref':ref(sp),'config_ref':s['config_ref'],'payload_ref':s['payload_ref'],'pins_rehashed':len(p['pins']),'source_inventory_pins':sum(x.startswith('source-inventory:') for x in roles),'target_inventory_pins':sum(x.startswith('target-inventory:') for x in roles),'all_binding_fields_match':True,'intentional_negative':'Exact legacy recovery grant schema/purpose with empty tuple; expected pause verifier signature-purpose rejection; all present root/database bindings match','remaining_seconds':(expires-now).total_seconds(),'private_credentials_read':False,'signed':False,'published':False,'formal_increment':0}
with (E/'root-grant-inspection.json').open('x',encoding='utf8') as w:json.dump(out,w,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
