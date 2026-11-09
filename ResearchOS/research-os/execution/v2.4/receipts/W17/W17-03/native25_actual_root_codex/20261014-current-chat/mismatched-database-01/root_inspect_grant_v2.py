import datetime,hashlib,json,sys,types
from pathlib import Path
E=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf8'))
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
def check(v):
 p=Path(v['path']);assert ref(p)['sha256']==v['sha256'] and p.stat().st_size==v['bytes'];return p
assert len(sys.argv)==2
sp=Path(sys.argv[1]).resolve();assert sp.parent==E/'controller'
s=load(sp);p=load(check(s['payload_ref']));f=load(check(s['fixture_public_ref']));r=load(E/'harness/rehearsal.public.json');b=p['binding']
assert s['phase']=='grant' and s['case']=='mismatched-database' and s['job_binding_id']==load(E/'controller/controller.started.json')['job_binding_id']
assert s['snapshot_guard_cleanup']['closed'] and not s['snapshot_guard_cleanup']['errors'] and all(x['matches'] for x in s['declared_pin_observations'])
assert p['schema']=='researchos.pause-schema-migration-grant.v1' and p['purpose']=='RESEARCHOS_RUNTIME_PAUSE_SCHEMA24_TO25_V1' and p['stage']=='APPLY_ORIGINAL'
assert p['release_sha256']==sha((Path(s['signed_destination']).parent/'recovery-release.json').read_bytes()) and len(bytes.fromhex(p['nonce']))==32
now=datetime.datetime.now(datetime.timezone.utc);issued=datetime.datetime.fromisoformat(p['issued_utc']);expires=datetime.datetime.fromisoformat(p['expires_utc']);assert issued<=now<expires and 0<(expires-issued).total_seconds()<=240
assert b['plan_id']=='schema24-to25-runtime-pause-v1' and b['owner_root']==f['owner_root'] and b['project_id']==f['project_id']
assert b['root']==f['root'] and b['database']==f['database'] and b['root_identity']==s['measured_native_ids']['root'] and b['database_identity']!=s['measured_native_ids']['database']
cfg=load(E/'controller.public.config.json');cp=Path(cfg['ControllerSource']['path']);assert sha(cp.read_bytes())=='sha256:c95ed27b644368fd846bd5ddbd4fc8268cbfea65eb2a8165691456e707a221fa'
m=types.ModuleType('root_public_native_id');m.__file__=str(cp);sys.modules[m.__name__]=m;exec(compile(cp.read_bytes(),str(cp),'exec'),m.__dict__)
temp=Path(cfg['Environment']['TEMP']).resolve();others=list(temp.rglob('other-native-file-*'));assert len(others)==1
other=others[0];assert other.is_file() and not other.is_symlink() and other.resolve().is_relative_to(temp)
other_id=m.native_file_id(other,False); database_id=m.native_file_id(Path(f['database']),False)
assert b['database_identity']==other_id and b['database_identity']!=database_id

for name,other_field in [('source_release_sha256','source_program_sha256'),('target_release_sha256','target_program_sha256'),('source_inventory_sha256','source_inventory_sha256'),('target_inventory_sha256','target_inventory_sha256'),('source_schema_sha256','source_schema_sha256'),('target_schema_sha256','target_schema_sha256'),('sql_sha256','sql_sha256'),('original_rows_sha256','original_rows_sha256'),('options_sha256','options_sha256')]:assert b[name]==r[other_field]
assert b['sql_sha256']=='sha256:6f3f90671170df80dcb4a8f6e8c8679f85cd03802399e821ed5478dde49e2ac0' and p['options']==r['options']
assert b['original_rows_sha256']==sha((E/'harness/before.rows.json').read_bytes())
for pin in p['pins']+[b['backup'],b['rehearsal']]:check(pin)
roles=[v['role'] for v in p['pins']];assert len(roles)==len(set(roles))
for role in ['target-rehearsal-program','handoff-binding','backup-producer-stdout','backup-producer-observation','source-program','target-program','migration-sql','encrypted-backup-manifest','isolated-restore-rehearsal']:assert role in roles
assert sum(x.startswith('source-inventory:') for x in roles)>0 and sum(x.startswith('target-inventory:') for x in roles)>0 and sum(x.startswith('encrypted-backup-payload:') for x in roles)>0
assert Path(s['signed_destination']).name=='current-schema24-to25-grant.json' and s['sign_kind']=='pause-migration-grant'
out={'schema':'researchos.root-native-concrete-grant-inspection/1','at':now.isoformat(),'snapshot_ref':ref(sp),'config_ref':s['config_ref'],'payload_ref':s['payload_ref'],'pins_rehashed':len(p['pins'])+2,'source_inventory_pins':sum(x.startswith('source-inventory:') for x in roles),'target_inventory_pins':sum(x.startswith('target-inventory:') for x in roles),'all_binding_fields_match':False,'intentional_database_identity_mismatch_only':True,'all_other_binding_fields_match':True,'other_native_file':str(other),'other_native_file_id':other_id,'actual_database_id':database_id,'remaining_seconds':(expires-now).total_seconds(),'private_credentials_read':False,'signed':False,'published':False,'formal_increment':0}
with (E/'root-grant-inspection.json').open('x',encoding='utf8') as w:json.dump(out,w,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=True))
