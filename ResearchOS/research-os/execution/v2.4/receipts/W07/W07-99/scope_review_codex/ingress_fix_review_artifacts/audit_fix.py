import collections, datetime, hashlib, json, pathlib, shutil, sqlite3, subprocess
ROOT=pathlib.Path(__file__).resolve().parents[7]
CAND=ROOT/'.local/worktrees/codex-w0799'
OUT=pathlib.Path(__file__).parent
EVID=CAND/'execution/v2.4/receipts/W07/W07-99/source_executor_codex'
RUN=EVID/'run-8017e0f7e4384703b223c3dbc542a057'
COMMIT='49143af141255f65465154d14e255852ff66b897'
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def dump(name,o):
 p=OUT/name;p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return {'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':sha(p.read_bytes())}
def git(*a):return subprocess.check_output(['git','-C',str(CAND),*a])
assert git('rev-parse','HEAD').decode().strip()==COMMIT
assert not git('status','--porcelain').strip()
paths=git('diff','--name-only','96efe3b42b52d2dbe0ab85bde803a3ebf0ac07aa^',COMMIT).decode().splitlines()
blobs={}
for p in paths:
 b=git('show',f'{COMMIT}:{p}');assert b==(CAND/p).read_bytes(),p;blobs[p]=sha(b)
scope=json.loads((ROOT/'execution/v2.4/receipts/W07/W07-99/integration_codex/complete_source_scope_codex.json').read_bytes())
amend=json.loads((ROOT/'execution/v2.4/receipts/W07/W07-99/scope_review_codex/scope_amendment_health_replay_x_marker.json').read_bytes())
allowed=scope['exact_paths']+[x['path'] for x in amend['additional_source_paths']]+['internal/domain/operations.go']
sources=[p for p in paths if not p.startswith('execution/')]
assert sorted(sources)==sorted(allowed)
proof=json.loads((RUN/'proof.json').read_bytes()); refs={}
def walk(o):
 if isinstance(o,dict):
  if set(['path','sha256'])<=set(o) and o['path'].startswith('execution/'):
   p=CAND/o['path'];assert p.resolve().is_relative_to(EVID.resolve());assert sha(p.read_bytes())==o['sha256'];refs[o['path']]=o['sha256']
  for v in o.values():walk(v)
 elif isinstance(o,list):
  for v in o:walk(v)
walk(proof)
before=json.loads((RUN/'source-before.json').read_bytes());after=json.loads((RUN/'source-after.json').read_bytes());assert before==after
for p,h in before.items():assert sha((CAND/p).read_bytes())==h,p
invocations=[]
for p in sorted(EVID.rglob('*.invocation.json')):
 v=json.loads(p.read_bytes());invocations.append({'path':str(p.relative_to(CAND)).replace('\\','/'),'sha256':sha(p.read_bytes()),'exit_code':v.get('exit_code'),'timed_out':v.get('timed_out'),'keys':list(v)})
vectors={'candidate':COMMIT,'commit_file_count':len(paths),'source_file_count':len(sources),'receipt_file_count':len(paths)-len(sources),'full_commit_blobs':blobs,'proof_sha256':sha((RUN/'proof.json').read_bytes()),'verified_proof_refs':refs,'source_manifest_files':len(before),'source_drift':[],'all_recorded_invocations':invocations}
dump('candidate_evidence_audit.json',vectors)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');checkout=ROOT/'.local'/('w07-ingress-fix-independent-review-'+stamp);checkout.mkdir()
copied={}
for root in ['internal','adapters','ops','migrations','spec/v2.0/contracts','evaluation','tests/sources']:
 for p in (CAND/root).rglob('*'):
  if not p.is_file() or '__pycache__' in p.parts:continue
  rel=p.relative_to(CAND);b=p.read_bytes();target=checkout/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);copied[str(rel).replace('\\','/')]=sha(b)
for name in ['go.mod','go.sum']:
 b=(CAND/name).read_bytes();(checkout/name).write_bytes(b);copied[name]=sha(b)
assert all(sha((CAND/p).read_bytes())==h for p,h in copied.items())
dump('replay_inputs.json',{'checkout':str(checkout),'source_hashes':copied,'candidate':COMMIT,'snapshot_drift':[],'purpose':'Independent local fixture replay and added negative review probe only; no source repair or external calls'})
print(json.dumps({'commit_files':len(paths),'source_files':len(sources),'proof_refs':len(refs),'manifest_files':len(before),'checkout':str(checkout)}))
