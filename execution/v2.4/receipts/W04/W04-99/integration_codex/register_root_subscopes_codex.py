"""Register root's disjoint external fixture and generic read-only accounting paths."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
V24=ROOT/'execution/v2.4';SPEC=ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cp_path,state_path,path_path=(V24/n for n in ['checkpoint.json','step_state.json','path_ownership.json'])
cp,paths=load(cp_path),load(path_path);state_raw=state_path.read_bytes()
assert cp['revision']==214 and paths['revision']==49 and len(cp['failure_counters'])==73
old_failures=copy.deepcopy(cp['failure_counters'])
arch=HERE.parent/'independent_formal_accounting_architecture_codex.json'
assert sha(arch)=='fa07c6bff03a5d7a5654309ce6b870bee0947af3d39934cda9e5705de456786c'
assert load(arch)['reviewer']=='codex:/root/w1702_review'
external='tests/context/parent/w0499_test.go'
shared_existing=['bootstrap/v24_checkpoint.py','execution/v2.4/parent_gate_ledger.py']
shared_new='execution/v2.4/formal_case_index.py'
assert not (ROOT/shared_new).exists()
candidate=ROOT/'.local/worktrees/codex-w0299'
assert not (candidate/external).exists()
binding=paths['card_path_bindings']['W04-99']
assert external in binding['paths']
binding['paths'].remove(external)
binding['root_only_paths'].extend([external,*shared_existing,shared_new])
binding['subtasks']['external_inventory_fixture']={'owner':'codex:/root','worktree':'.local/worktrees/codex-w0299','paths':[external],
    'scope':'Actual current service/host native-choice/real Scanner and Authority two-project FIXTURE A01-04, replay/continuation/isolation/rollback. W1102 must not edit this file; root source/test contribution remains subject to independent W1702 review.'}
binding['subtasks']['generic_formal_accounting']={'owner':'codex:/root','workspace':'main','paths':[*shared_existing,shared_new],
    'scope':'Generic pure derivation from canonical independently registered final-owner receipts, with explicit protocol adapter; no import of a W04 construction driver/validator and no manually edited case status store.'}
now=dt.datetime.now(dt.timezone.utc).isoformat()
record=HERE/'root_subscopes_codex.json'
save(record,{'schema':'researchos.root-disjoint-subscope.v1','step_id':'W04-99','registered_at':now,'actor':'codex:/root',
    'independent_accounting_architecture':ref(arch),'external_test_subscope':binding['subtasks']['external_inventory_fixture'],
    'shared_existing_sha256':{p:sha(ROOT/p) for p in shared_existing},'new_shared_path':shared_new,
    'generic_constraints':['Never infer case acceptance from parent status or reachable selector alone.','Frozen42 cases/22parents and final owners agree across authoritative contracts.',
        'Only canonical accepted owner-99 registered review/context/actual observed independent issuance refs can count; exact mode/full assertion IDs/commands/current complete inputs/independent semantic verdict required.',
        'Invalid/partial/stale/unsupported owners are isolated with reasons, never erase historical raw or reset counters; corrupt global authority returns structured INVALID.',
        'Read-only authority inputs, preserve existing ledger derived-output interface and checkpoint history/U09 selection/streak thresholds. No new manual ledger.',
        'No public helper import of W04 construction validator/driver. Explicit bounded protocol adapter can support existing W04 shape; unsupported future protocol fails closed.',
        'Meaningful synthetic integrity/aggregation tests in owned receipts; product cases/modes/identities never synthesized as real PASS.'],
    'formal_case_count_delta':0,'parent_accepted':False})
paths.update(revision=50,amended_at=now,amended_by='codex:/root',updated_at=now,updated_by='codex:/root');replace(path_path,paths)
cp.update(updated_at=now,updated_by='codex:/root',note='W04 current source/test and formal integrity implementation in progress. Root external inventory test subowner and3 generic accounting paths registered before edits; primary worker remains disjoint. Parent4/22 formal0/42,73 failures unchanged.')
cp['integrity_events'].append({'at':now,'actor':'codex:/root','event':'W04_ROOT_DISJOINT_SUBSCOPES_REGISTERED','evidence':ref(record)})
cp['evidence_index'].append(record.relative_to(ROOT).as_posix());replace(cp_path,cp)
event=HERE/'root_subscope_value_round_codex.json'
save(event,{'schema':'researchos.value-round.v1','round_id':'W04-root-external-test-and-formal-accounting-scope-20261006','delta':'INFRASTRUCTURE',
    'summary':'Disjoint root current inventory fixture and independently designed generic canonical formal accounting paths registered before implementation; no formal cases accepted.',
    'evidence_refs':[ref(record),ref(arch)]})
argv=[sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),'--checkpoint',str(cp_path),'--state',str(state_path),
    '--plan',str(SPEC/'contracts/execution.plan.json'),'--delivery',str(SPEC/'contracts/delivery.contract.json'),'--expected-revision','214','--round-event',str(event),'--actor','codex:/root']
r=subprocess.run(argv,cwd=ROOT,capture_output=True)
(HERE/'checkpoint215.stdout.txt').write_bytes(r.stdout);(HERE/'checkpoint215.stderr.txt').write_bytes(r.stderr)
assert r.returncode==0,r.stderr.decode('utf8','replace')
after=load(cp_path);assert after['revision']==215 and after['failure_counters']==old_failures and state_path.read_bytes()==state_raw
print(json.dumps({'status':'PASS_ROOT_DISJOINT_SCOPES','checkpoint':215,'path_revision':50,'formal_accepted':0,'failure_origins':73}))
