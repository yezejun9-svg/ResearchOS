import hashlib,json
from pathlib import Path
C=Path(__file__).resolve().parent.parent
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/product-v1/receipts/single-harness-20261104'
P=B/'progress-cp693'
I=B/'workbench-assistant-refinement/integration'
seen={}
def sha(p):
 h=hashlib.sha256(p.read_bytes()).hexdigest();seen[str(p)]=h;return h
def read(p):
 sha(p);return json.loads(p.read_bytes())
cp=read(R/'execution/v2.4/checkpoint.json');state=read(R/'execution/product-v1/state.json');leases=read(R/'execution/product-v1/leases.json');progress=read(P/'RESUME.json');memory=read(P/'MEMORY.json')
oldcp=read(P/'checkpoint.before.json');oldstate=read(P/'state.before.json');oldleases=read(P/'leases.before.json')
assert cp['revision']==693 and oldcp['revision']==692 and leases['revision']==33 and oldleases['revision']==32
assert cp['current_Main_HEAD']==progress['main_head']=='360c3eefd06ba82255352357c05ece00dae00d3a'
assert cp['failure_counters'][:len(oldcp['failure_counters'])]==oldcp['failure_counters'] and len(oldcp['failure_counters'])==2646 and len(cp['failure_counters'])==2648
assert state['status']==progress['status']==cp['current_implementation']['status']=='WORKBENCH_SOURCE_INTEGRATED_BUILD14_BLOCKED_SYSTEM_COMMIT_MEMORY'
assert state['active_scopes']==leases['source_owners'] and not [e for e in leases['source_owners'] if e['status']=='IMPLEMENTING']
assert state['integrated_source']==oldstate['integrated_source']
pins={k:v for row in state['integrated_source'] for k,v in row['source_sha256'].items()}
union=hashlib.sha256(json.dumps(pins,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert len(pins)==70 and union==progress['source_union_sha256']=='954c293b52e5b83dcb8a779410e89fc3c74a4bad3550d3620ba0938cc67e15c2'
for ref,h in pins.items():assert sha(R/ref)==h,ref
plan=read(C/'product-v1-workbench-refinement-integration-plan.json');integ=read(I/'integration.json');journal=read(I/'newline-resume/journal.json')
assert integ==read(I/'RESUME.json') and integ['main_head']==progress['main_head'] and integ['checkpoint_revision']==692
assert journal['status']=='SOURCE_COMMIT_CHECKPOINT_SAVED' and journal['checkpoint_revision']==692 and journal['main_head']==progress['main_head']
review=read(R/integ['review_ref']);assert sha(R/integ['review_ref'])==integ['review_sha256']=='4a79141a4c140828486a48b79547844b8e78f6851a8b20214f5433ac159bd4be'
assert integ['source_sha256']==review['source_sha256']
for ref,h in integ['source_sha256'].items():assert sha(R/ref)==h
for ref,h in plan['protected_sha256'].items():assert (sha(R/ref) if (R/ref).is_file() else 'ABSENT_BEFORE')==h
assert (I/'root-integration-journal.json').read_bytes()==(I/'newline-resume/original-journal.json').read_bytes()
assert (C/'product-v1-workbench-refinement-integration-plan.json').read_bytes()==(I/'newline-resume/original-plan.json').read_bytes()
for f in ['checkpoint.before.json','state.before.json','root-integration-journal.json','newline-resume/original-plan.json','newline-resume/original-journal.json','newline-resume/amended-plan.json']:sha(I/f)
assert read(I/'checkpoint.before.json')['revision']==691
handoff=(R/'execution/v2.4/HANDOFF_RESUME_PACK.md').read_bytes();prior=(P/'handoff.before.md').read_bytes();assert handoff.startswith(b'# Current resume CP693') and handoff.endswith(prior)
sha(R/'execution/v2.4/HANDOFF_RESUME_PACK.md');sha(P/'handoff.before.md')
assert memory==progress['memory'] and memory['available_commit_bytes']==593276928 and memory['process_or_os_changes']==0
assert progress['real_model_requests']==integ['real_model_requests']==2 and progress['new_native_model_calls']==0
assert progress['root_running_long_commands']==[] and progress['active_source_owners']==[]
absent=[R/'.local/worktrees/product-v1-build-14-20261105',B/'build14-scope',C/'product-v1-owned-verification-20261104/scopes/product-v1-build-14.json',C/'product-v1-owned-verification-20261104/runs/product-v1-build-14']
assert not any(p.exists() for p in absent)
archives=[]
for a in [B/'post-ui-integration-ready-for-build14',B/'workbench-assistant-refinement/tests03-evidence',B/'workbench-assistant-refinement/vite01-evidence']:
 m=read(a/'ROOT_ARCHIVE.json')
 for row in m['files']:
  assert sha(a/row['path'])==row['sha256'],row['path']
  assert sha(Path(m['source'])/row['path'])==row['sha256'],row['path']
 archives.append(dict(path=str(a),manifest_sha256=sha(a/'ROOT_ARCHIVE.json'),files=len(m['files']),both_C_D_verified=True))
jobs=[]
for rp in [B/'workbench-assistant-refinement/tests03-evidence/run/RESULT.json',B/'workbench-assistant-refinement/vite01-evidence/owned-run/RESULT.json',C/'product-v1-owned-verification-20261104/runs/product-v1-visual12-purechecks-01/RESULT.json']:
 j=read(rp)
 assert j['status']=='COMPLETED_OWNED_JOB_STOPPED' and j['root_exit_code']==0 and j['job_active_zero'] and j['stop_proved'] and j['root_signaled']
 assert not j['input_drift'] and not j['timed_out'] and not j['errors'] and j['terminate_job_attempts']==j['terminate_original_root_attempts']==0
 assert j['close_order']==['job','thread','process']
 for row in j['raw']:assert sha(rp.parent/row['file'])==row['sha256']
 jobs.append({k:j[k] for k in ['scope_id','scope_sha256','job_total_processes','root_pid','creation_filetime','root_exit_code','job_active_zero','stop_proved','close_order','elapsed_seconds']})
assert (C/'record_product_v1_cp693_resource_checkpoint.py').read_bytes()==(P/'record_product_v1_cp693_resource_checkpoint.py').read_bytes()
sha(C/'record_product_v1_cp693_resource_checkpoint.py');sha(C/'product_v1_memory_readback.py')
result=dict(status='PASS_READONLY_FILE_AUDIT',head=progress['main_head'],checkpoint=693,lease_revision=33,active_implementing=0,history_before=2646,history_after=2648,history_prefix_unchanged=True,appended_origins=[v['origin_key'] for v in cp['failure_counters'][2646:]],source_count=70,source_union_sha256=union,source_sha256=integ['source_sha256'],protected_count=len(plan['protected_sha256']),memory=memory,jobs=jobs,archives=archives,build14_absent=[str(p) for p in absent],evidence_sha256=seen)
with (O/'READBACK.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['evidence_sha256','source_sha256']},ensure_ascii=False))
