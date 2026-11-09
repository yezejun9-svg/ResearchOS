import collections, datetime, hashlib, json, pathlib, subprocess, sys

base=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
work=repo/'.local/worktrees/verifier-replacement-20261014'
def git(*args): return subprocess.check_output(['git',*args],cwd=work)
def pin(p):
    raw=p.read_bytes()
    return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def write(p,data):
    with p.open('x',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
def tracked():
    names=git('ls-files','-z').decode('utf-8').split('\0')
    return {n:pin(work/n) for n in names if n and (work/n).is_file()}
if sys.argv[1]=='snapshot':
    write(base/'08-before-commit-build-inputs.json',tracked())
    print('source input hashes saved before commit/build')
    sys.exit(0)
scope_path=repo/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261014-current-chat/continuation-cp487/verifier-replacement-revision01-scope.json'
scope=json.loads(scope_path.read_text('utf-8'))
head=git('rev-parse','HEAD').decode().strip()
tree=git('rev-parse','HEAD^{tree}').decode().strip()
assert not git('status','--porcelain=v1').strip()
changed=git('diff','--name-only',scope['base_commit'],head).decode().splitlines()
assert set(changed)<=set(scope['allowed_source_files']) and len(changed)==4
all_changed=git('diff','--name-only','c8b7adab9f0c15eb33f235f8d0d9eb205794e376',head).decode().splitlines()
assert set(all_changed)==set(scope['allowed_source_files'])
inputs=tracked()
assert inputs==json.loads((base/'08-before-commit-build-inputs.json').read_text('utf-8'))
write(base/'12-after-commit-build-inputs.json',inputs)
old_pins=json.loads((base/'02-baseline-pins.json').read_text('utf-8'))
for old in old_pins: assert pin(pathlib.Path(old['path']))==old,old['path']
write(base/'12-preserved-evidence-check.json',{'verified':len(old_pins),'unchanged':True,'pins':pin(base/'02-baseline-pins.json')})
for filename, revision_base in [('12-revision.patch',scope['base_commit']),('12-exact8.patch','c8b7adab9f0c15eb33f235f8d0d9eb205794e376')]:
    with (base/filename).open('xb') as f: f.write(git('diff','--binary','--full-index',revision_base,head))
tests={}
for p in sorted(base.glob('*.log')):
    events=[]
    for line in p.read_text('utf-8').splitlines():
        try: ev=json.loads(line)
        except json.JSONDecodeError: continue
        if isinstance(ev,dict):events.append(ev)
    if not any('Action' in e for e in events):continue
    tests[p.name]={'top_level':dict(collections.Counter(e['Action'] for e in events if e.get('Test') and '/' not in e['Test'] and e.get('Action') in ['pass','fail','skip'])),'including_subtests':dict(collections.Counter(e['Action'] for e in events if e.get('Test') and e.get('Action') in ['pass','fail','skip'])),'failures':[e.get('Test','PACKAGE') for e in events if e.get('Action')=='fail'],'skips':[e.get('Test','PACKAGE') for e in events if e.get('Action')=='skip']}
summary={'state':'CANDIDATE_FOR_INDEPENDENT_REVIEW','source_commit':head,'source_tree':tree,'revision_base':scope['base_commit'],'revision_paths':changed,'cumulative_exact8_paths':all_changed,'formal_increment':0,'product_execution':False,'independent_acceptance':False,'changes':{'F1':'Plan v2 persists history_sequence and predecessor operation/plan/terminal hash. Every terminal including ABORTED extends the verified immutable head; event sequence/previous/hash determine order, At is parsed for audit validity only. Startup, commit and recovery reject forks, cycles, missing predecessors and digest drift. Same old bytes after a round trip cannot revive a stale plan.','F2':'All reserved local-verifier principals, grants and lineage are validated before ownership filtering; missing/invalid/orphan/derived-ID mismatch rejects. Structurally complete foreign service roots and children may retain revocation but are bound into the snapshot digest and confer no authority over this registration.'},'tests':tests,'failures_preserved':['Original author EARLY-FAILURES and all failed attempts, original 3 independent adversarial failures, and legacy asset supplement remain byte-identical.','03-new-regression: 3 top-level / 10 leaf failures arose from using the original first-operation preflight helper during reverse setup; it asserts journal root absent. Reverse setup now invokes preflight directly, preserving the first-operation helper assertion. Full logs remain.'],'diagnostics':['Initial parent AGENTS.md path absent; repository AGENTS.md read.','Initial scope hash path had excess parent segment; canonical path fixed and pinned hash verified.','An optional main-repo test-file read returned missing because source is in independent worktree.','rg literal wildcard path rejected by Windows; corrected to -g search.','Read-only git diff --check was accidentally invoked in main repo and returned missing object 6140a5b5ead748e28487b78a777bf9c8d07192e8. Root notified; no shared Git repair attempted. Independent worktree diff check succeeds.'],'remaining':['Foreign-owner negative remains SKIP without WRITE_OWNER; not passed.','Native process kills establish process-crash recovery, not machine power-loss durability.','Unbound v1 draft replacement plans fail closed; old immutable history is never rewritten or migrated. No actual product replacement history was touched.','Product packaging, original DataRoot replacement, new qualification and formal acceptance remain Root-owned future work.','Earlier recursive fixture cleanup was rejected by automatic policy; no retry or workaround performed.'],'source_guard':{'tracked_present_files':len(inputs),'before_after_equal':True,'old_evidence_unchanged':len(old_pins)}}
write(base/'12-SUMMARY.json',summary)
manifest={'schema':'researchos.runtime-verifier-replacement-revision-manifest/1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':head,'source_tree':tree,'scope':pin(scope_path),'source_files':{n:pin(work/n) for n in all_changed},'revision_patch':pin(base/'12-revision.patch'),'cumulative_patch':pin(base/'12-exact8.patch'),'go':pin(repo/'.local/tools/go1.27.1/go/bin/go.exe'),'control_fixture_binary':pin(repo/'.local/tmp/verifier-replacement-20261014/control-revision01-final.exe'),'receipts':{p.name:pin(p) for p in sorted(base.iterdir()) if p.is_file()},'formal_increment':0}
write(base/'12-FINAL-manifest.json',manifest)
print(json.dumps({'commit':head,'tree':tree,'manifest':pin(base/'12-FINAL-manifest.json'),'tests':tests},ensure_ascii=False,indent=2))
