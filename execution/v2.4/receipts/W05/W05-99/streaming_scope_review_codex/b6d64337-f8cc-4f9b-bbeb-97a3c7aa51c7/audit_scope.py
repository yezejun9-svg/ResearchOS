import hashlib, json, pathlib, subprocess
from datetime import datetime, timezone

OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/codex-w0599-command-queue'
REL='execution/v2.4/receipts/W05/W05-99/streaming_scope_readonly_b2ee436f-d914-43ea-acdd-44ce34aec470'
D=WT/REL
COMMIT='ef4e1ba03431305351cef58137e64c5de24a8e6c'
def sha(b): return hashlib.sha256(b).hexdigest()
def ref(p): return {'path':str(p),'sha256':sha(p.read_bytes())}
def git(*args):
 r=subprocess.run(['git','-C',str(WT),*args],capture_output=True,check=True)
 return r.stdout
h=json.loads((D/'handoff.json').read_bytes())
receipt_checks=[]
for name,entry in h['files'].items():
 p=D/name; b=p.read_bytes()
 assert sha(b)==entry['sha256'] and len(b)==entry['bytes'],name
 receipt_checks.append(ref(p))
before=json.loads((D/'input_manifest_before.json').read_bytes())
after=json.loads((D/'input_manifest_after.json').read_bytes())
assert before==after and len(before)==48
current=[]
for name,entry in before.items():
 p=ROOT/name; b=p.read_bytes()
 current.append({'path':name,'actual_sha256':sha(b),'expected_sha256':entry['sha256'],'matches':sha(b)==entry['sha256'],'bytes':len(b)})
assert all(x['matches'] for x in current)
blobs=[]
for name in git('diff-tree','--no-commit-id','--name-only','-r',COMMIT).decode('utf8').splitlines():
 assert name.startswith(REL+'/'),name
 raw=git('show',COMMIT+':'+name)
 assert raw==(WT/name).read_bytes(),name
 blobs.append({'path':name,'sha256':sha(raw),'bytes':len(raw)})
additional=['AGENTS.md','internal/api/contracts/client.protocol.schema.json','internal/domain/client_command_queue.go','internal/domain/runtime_session_events_windows.go','third_party/mu/packages/ai/src/utils/event-stream.ts','third_party/mu/packages/ai/src/api/simple-options.ts','.local/worktrees/v24-continuation/spec/v2.4/19_DESKTOP_IMPLEMENTATION_BLUEPRINT.md']
extra=[ref(ROOT/p) for p in additional]
schema=json.loads((ROOT/'internal/api/contracts/client.protocol.schema.json').read_bytes())
frozen=json.loads((ROOT/'.local/worktrees/v24-continuation/spec/v2.4/contracts/client.protocol.schema.json').read_bytes())
assert schema==frozen
proposal=json.loads((D/'proposal.json').read_bytes())
assert len(proposal['exact_proposed_source_scope'])==19
result={'schema':'researchos.w05.independent-streaming-scope-audit.v1','reviewer_id':'codex:/root/w05_merge_review','created_at':datetime.now(timezone.utc).isoformat(),'candidate_commit':COMMIT,'proposal_ref':ref(D/'proposal.json'),'handoff_ref':ref(D/'handoff.json'),'receipt_hash_checks':receipt_checks,'commit_blobs':blobs,'inputs':current,'additional_read_inputs':extra,'schema_semantic_exact':True,'main_head_at_audit':subprocess.run(['git','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True,check=True,text=True).stdout.strip(),'proposal_scope':proposal['exact_proposed_source_scope'],'product_tests_executed':0,'network_calls':0,'source_canonical_registry_changes':0,'formal_acceptance_delta':0}
raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf8')
with (OUT/'audit.json').open('xb') as f:f.write(raw)
print(json.dumps({'audit_sha256':sha(raw),'inputs':len(current),'commit_blobs':len(blobs),'drift':sum(not x['matches'] for x in current),'proposal_sha256':result['proposal_ref']['sha256'],'handoff_sha256':result['handoff_ref']['sha256']}))
