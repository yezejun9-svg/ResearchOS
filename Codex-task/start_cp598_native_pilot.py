import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
DESIGN = HERE / 'cp597-w14-next-scope'
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104'
HEAD = '001f7e5a4d95152c8f83874a60d9fbd3bbace538'
CORE_PROD = [
 'internal/host/native_client_attestation.go','internal/domain/client_writer_origin.go',
 'internal/host/host.go','internal/host/native.go','internal/host/contract.go',
 'internal/domain/client_protocol.go','internal/domain/client_protocol_auth.go','internal/domain/client_command_identity.go',
 'internal/api/v2.go','internal/api/server.go','internal/host/contracts/native.client-attestation.v1.schema.json',
 'apps/control/main.go','internal/domain/client_native_writer_origin_schema.go',
 'internal/domain/client_native_writer_origin_store.go','internal/domain/backup_client_native_writer_origins.go',
 'internal/domain/contracts/0025_client_native_writer_origins.sql','internal/domain/backup.go',
]
CORE_TESTS = [
 'internal/host/native_client_attestation_test.go','internal/domain/client_writer_origin_test.go',
 'internal/api/v2_native_create_test.go','internal/domain/client_native_writer_origin_store_test.go',
 'internal/domain/backup_client_native_writer_origins_test.go',
]
CLIENT_PROD = ['apps/cli/cli_native.go','apps/cli/cli_v2.go','apps/cli/cli_verbs.go',
 'apps/desktop/main/main.js','apps/desktop/main/lib/native.js','apps/desktop/main/lib/http-wire.js','apps/desktop/main/lib/ipc.js']
CLIENT_TESTS = ['apps/cli/cli_native_attestation_test.go','tests/ui/native-create-attestation-fixture.cjs']


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def git(cwd,*args):
 return subprocess.check_output(['git','-c','gc.auto=0','-c','maintenance.auto=false','--no-optional-locks',*args],cwd=cwd,stderr=subprocess.STDOUT).decode('utf-8')
def put(p,v):
 t=p.with_name(p.name+'.new'); assert not t.exists()
 t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); os.replace(t,p)


cpfile=ROOT/'execution/v2.4/checkpoint.json'; raw=cpfile.read_bytes(); cp=json.loads(raw)
assert cp['revision']==597 and len(cp['failure_counters'])==2433
assert cp['project_id']=='aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
assert git(ROOT,'rev-parse','HEAD').strip()==HEAD and not OUT.exists()
assert len(CORE_PROD)==17 and len(CORE_TESTS)==5 and len(CLIENT_PROD)==7 and len(CLIENT_TESTS)==2
assert not set(CORE_PROD+CORE_TESTS).intersection(CLIENT_PROD+CLIENT_TESTS)
paths=CORE_PROD+CORE_TESTS+CLIENT_PROD+CLIENT_TESTS
dirty=set(git(ROOT,'diff','--name-only').splitlines()); assert not dirty.intersection(paths)
protected=json.loads((ROOT/'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for p,d in protected.items(): assert (sha(ROOT/p) if (ROOT/p).is_file() else 'ABSENT_BEFORE')==d,p
assert sha(DESIGN/'SCOPE_PROPOSAL.json')=='a71890f14f45af5492afb6ed074c1b6dd4cdb9906726ebd0aae88cad87448c97'
OUT.mkdir(); (OUT/'checkpoint.cp597.before.json').write_bytes(raw)
(OUT/'design').mkdir(); (OUT/'reviews').mkdir(); (OUT/'root').mkdir()
for name in ('SCOPE_PROPOSAL.json','DTO.proposal.json','NEXT_SCOPE.md','source-index.json','manifest.json'):
 (OUT/'design'/name).write_bytes((DESIGN/name).read_bytes())
now=datetime.now(timezone.utc).isoformat()
shared={
 'base_head':HEAD,'at':now,'integrator':'codex:/root','formal_increment':0,'counter_reset':False,
 'purpose':'Fresh session.create Native origin pilot; not full W14 handoff.',
 'wire_profile':json.loads((DESIGN/'DTO.proposal.json').read_bytes()),
 'root_decisions':[
  'Private Native request/result only; original three actions, public client.protocol/2 schema and ordinary envelope unchanged.',
  'X-ResearchOS-Native-Attestation is an untrusted ref selector; only current typed OS peer -> private immutable bounded Host map witness -> exact raw/bearer/domain auth facts can authorize fresh origin.',
  'Map capacity256, TTL at most120s or actual credential expiry, no raw credential retained/logged, no bootstrap/renew/issue/revoke by attestation.',
  'Client production default is legacy-compatible, zero new calls/bytes when RESEARCHOS_NATIVE_CREATE_PILOT is not1. Explicit gate1 requires proof and unsupported/failure is NOT_SENT with no legacy fallback.',
  'Fresh COMPLETED create only: original handler/typed response/identity sealed-v1, insert origin, exact private-header v1->v2 CAS, revalidate pair in same Tx before commit. REJECTED stays v1/no origin.',
  'Original sealed COMPLETED replay never creates grant/witness consumption/event. Native v2 marker/row/original raw+typed response mismatch is integrity error, not legacy.',
  'For every origin-bearing session foreign attach is refused for live/expired/null lease before legacy branch; map loss/restart never downgrades it. Legacy unproved sessions keep current behavior, not claimed globally safe.',
  'same-writer attach and goal.start gain no new origin/rebind. No crosswriter ACK/CAS or active Run pause in this slice.',
  'Candidate0025 payload is reserved only at internal/domain/contracts/0025_client_native_writer_origins.sql, outside live migration scan. No change to max24 or ordinary startup, no automatic schema installation.',
  'Prepared addon is enabled only explicitly in fresh test/controlled code. Never-adopted schema is UNSUPPORTED; adopted/marked missing or drift is integrity failure. Ordinary backup/restore with addon explicitly UNSUPPORTED until separately reviewed full adoption.',
  'Do not reinterpret missing rows as unused old native approval. No old UNKNOWN scope/model probe replay and no failure count reset.',
 ],
 'verification':'Locked offline Go/pure Node; injected peer and fresh SQLite/Recorder only. No live Native/HTTP/model/old DB/keys/provider call. Keep all failed attempts and source/raw/result pins.',
 'forbidden':['No existing database access or migration','No frozen external spec or public protocol schema edits','No real migration0025 file in migrations/sqlite','No model probe or paid/external calls','No second scheduler/current_ref/writer journal','No registry/step_state/path_ownership edits','No source edits outside exact scope or self-signed acceptance'],
}
workers=[]
for name,owner,prod,tests in (
 ('core','codex:/root/workbench_builder',CORE_PROD,CORE_TESTS),
 ('clients','codex:/root/runtime_readiness',CLIENT_PROD,CLIENT_TESTS),
):
 wt=ROOT/('.local/worktrees/w14-native-create-'+name+'-20261104'); assert not wt.exists()
 receipt=OUT/name; receipt.mkdir()
 for d in ('author','reviews','tools'): (receipt/d).mkdir()
 git(ROOT,'worktree','add','--no-checkout','-b','codex/w14-native-create-'+name+'-20261104',str(wt),HEAD)
 git(wt,'sparse-checkout','set','--no-cone','/AGENTS.md','/go.mod','/go.sum','/internal/','/adapters/','/apps/','/tests/ui/','/tests/runtime/','/migrations/sqlite/','/spec/v2.0/contracts/','/ops/')
 git(wt,'checkout','HEAD')
 evaluation=git(wt,'ls-tree','-r','--name-only','HEAD','--','evaluation/holdout/jev','evaluation/evolution','evaluation/skills').splitlines()
 selected=['/'+p for p in evaluation if p.endswith('.go') and not p.endswith('_test.go')]
 git(wt,'sparse-checkout','add',*selected)
 assert not git(wt,'status','--porcelain=v1','-uno').strip()
 baseline={p:sha(ROOT/p) if (ROOT/p).is_file() else 'ABSENT_BEFORE' for p in prod+tests}
 scope=dict(shared,scope_id='W14_NATIVE_CREATE_PILOT_'+name.upper()+'_V1',owner=owner,worktree=str(wt),production_paths=prod,test_paths=tests,baseline_sha256=baseline)
 put(receipt/'scope.json',scope)
 workers.append({'step_id':'W14-01','slice_id':scope['scope_id'],'owner':owner,'worktree':str(wt),'state':'SCOPED_SOURCE_IMPLEMENTATION_ONLY','scope_ref':str((receipt/'scope.json').relative_to(ROOT))})
put(OUT/'design/ROOT_DECISIONS.json',shared)
resume={'checkpoint_revision':598,'status':'IMPLEMENTING_FRESH_NATIVE_CREATE_PILOT_PREPARED_ADDON_ONLY','main_head':HEAD,
 'formal_accepted':0,'formal_required':42,'formal_increment':0,'failure_records':len(cp['failure_counters']),'counter_reset':False,
 'scopes':workers,'model_probe_replay_allowed':False,
 'next':'Implement exact22 core+9 client paths under two owners; lock private DTO/header/DDL interfaces, validate fresh fixtures, independently review, integrate serially. Prepared addon only; existing data untouched, native pilot gate default off. Full W14 and source Goal acceptance remain unfinished.'}
put(OUT/'RESUME.json',resume)
cp['revision']=598;cp['expected_previous_revision']=597;cp['updated_at']=now
cp['next_command']=resume['next']+' Read '+str((OUT/'RESUME.json').relative_to(ROOT))
cp['current_implementation']={'status':resume['status'],'at':now,'resume_ref':str((OUT/'RESUME.json').relative_to(ROOT)),'active_construction_owners':[w['owner'] for w in workers],'formal_increment':0}
cp['workers'].extend(workers)
assert cpfile.read_bytes()==raw;put(cpfile,cp)
handoff=ROOT/'execution/v2.4/HANDOFF_RESUME_PACK.md';before=handoff.read_bytes();(OUT/'handoff.cp597.before.md').write_bytes(before)
temp=handoff.with_name(handoff.name+'.cp598.new');assert not temp.exists()
temp.write_bytes(('# Current resume CP598\n\nRead '+str((OUT/'RESUME.json').relative_to(ROOT))+'. Two isolated Native fresh-create pilot source scopes (22core+9clients), default-off prepared addon. No old DB or real migration/model action. Historical failures/UNKNOWN and consumed model scope retained; formal0/42, full handoff closed.\n\n').encode()+before);os.replace(temp,handoff)
(OUT/'root/start_cp598_native_pilot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'checkpoint':598,'head':HEAD,'scopes':workers,'failure_records':len(cp['failure_counters']),'formal_increment':0}))
