from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
audit=read(OUT/'source-audit.json')
for row in audit['changed_paths']:assert sha(Path(row['overlay']))==row['sha256']
for row in audit['unchanged_package_paths']:assert sha(ROOT/row['path'])==row['working_sha256']
for row in audit['author_evidence']:assert sha(Path(row['copy']))==row['sha256']
assert read(OUT/'command.json')['exit_code']==0
assert read(OUT/'queued-command.json')['exit_code']==1
assertions=[]
tests=[]
for name in ['stdout.jsonl','queued.stdout.jsonl']:
 for line in (OUT/name).read_text().splitlines():
  event=json.loads(line);output=event.get('Output','')
  if output.startswith('S2_INDEPENDENT_ASSERT '):assertions.append(json.loads(output.removeprefix('S2_INDEPENDENT_ASSERT ')))
  if event.get('Action') in ['pass','fail'] and event.get('Test'):tests.append({'log':name,'test':event['Test'],'verdict':event['Action']})
assert len(assertions)==37
assert [r['id'] for r in assertions if r['status']=='FAIL']==['queued-write-honors-own-deadline']
finding={
 'id':'S2-ASYNC-001','priority':'P2','status':'OPEN',
 'title':'Queued Write ignores its own context deadline while waiting for the serial lock',
 'source':'ops/experiment_sandbox/async_windows.go','line':90,
 'trigger':'A live child does not consume stdin. A first 64KiB Write blocks while holding writeMu; a second Write has a 40ms deadline.',
 'observed':'The second Write remained blocked after 200ms, then returned process input closed only after explicit Process.Cancel killed the job and released the first writer.',
 'impact':'Concurrent protocol senders cannot rely on Write(ctx) to stop waiting at their own deadline. Queued senders may wait for the preceding writer (up to its 5-second cap) rather than returning their own cancellation.',
 'requested_fix':'Use cancellation-aware serialized write admission, select on caller context and process completion while waiting, and reject already-cancelled frames before launching the pipe write. Preserve one-frame-at-a-time writes and job cancellation for an in-flight blocked write.',
 'evidence':['queued-command.json','queued.stdout.jsonl','queued_write_test.go','native/queued-write.json'],
 'non_claim':'No isolation escape, real provider access, permanent process leak or deadlock is demonstrated. Explicit cancellation stopped the owned child and released both writers.'
}
limits=[
 'Only the native asynchronous AppContainer boundary at source 2f30646 is reviewed. No complete S2 coordinator/domain/typed-bridge/workbench acceptance, construction gate, LIVE or BOUNDED_AUTO qualification is granted.',
 'Three frozen source files are overlaid on main 33d9230. The two remaining package files match the frozen source after line-ending normalization; product source and the active author worktree were not edited.',
 'All native processes use newly created no-secret fixtures, fresh owned AppContainers and temporary directories. No protected production service, provider or external network destination is contacted.',
 'BeforeResume and OnStream are trusted host callbacks; this review exercises callback rejection and prompt consumption, not indefinitely hung arbitrary callback code. The API documents prompt stream consumption.',
 'Stream bounds are 4MiB per stream. A cancelled process can legitimately have drained EOF streams; callback rejection and stream overflow correctly produce StreamsDrained=false.',
 'Run compatibility covers ordinary completion, timeout and existing root-overlap refusal. The older TestNativeSandbox external-network probe was intentionally excluded because external access was outside this task.',
 'Three standard pipe handles remain the only explicit inherited handles; zero capabilities, minimal environment, active-process limit and private staging ACL logic were preserved by source comparison. Child host-canary/proxy environment absence and capabilities were also checked natively; arbitrary handle enumeration was not performed.',
 'The author original SetWriteDeadline failure and subsequent successful run are retained as immutable Git-sourced evidence. This review also retains the failing queued-deadline probe and does not report it as PASS.',
]
review={
 'artifact_kind':'INDEPENDENT_ASYNC_BOUNDARY_SLICE_REVIEW','verifier':'codex:/root/evolution_verifier',
 'source_revision':audit['source_revision'],'main_base':audit['main_head'],
 'verdict':'NEEDS_FIX_ASYNC_WRITE_CANCELLATION','maximum_acceptance_scope':'PASS_ASYNC_BOUNDARY_SLICE',
 'findings':[finding],'P1_findings':[],
 'validation':{'primary_command_exit':0,'primary_independent_assertions_pass':34,'targeted_command_exit':1,'targeted_assertions_pass':2,'targeted_assertions_fail':1,'total_independent_assertions_pass':36,'total_independent_assertions_fail':1,'tests':tests,'commands':['command.json','queued-command.json']},
 'passed_behaviors':[
  'Callback identity matches actual Windows process creation time/PID; an fsynced identity record and callback return timestamp precede the child first-execution timestamp.',
  'Vetoed suspended process emits no child output, publishes no output file, and is already terminated when Start returns an error.',
  'Eight concurrent bounded frames are delivered atomically and completely; timed-out Wait does not cancel the process, CloseInput ends stdin, post-close Write refuses, and repeated Wait returns the same completed result.',
  'A blocked 64KiB write hits a 100ms deadline, cancels the job, releases the writer and allows bounded Cancel/Wait without deadlock.',
  'A failing stream callback and stderr overflow stop the child, retain bounded evidence, and mark streams undrained.',
  'Normal and timed-out Run preserve expected exit behavior; process stopped, staging removed, and no capabilities granted.',
 ],
 'limits':limits,'source_and_author_evidence_unchanged':True,
 'whole_S2_accepted':False,'LIVE_qualified':False,'BOUNDED_AUTO_granted':False,
}
write(OUT/'review.json',review)
write(OUT/'all-assertions.json',assertions)
(OUT/'review.md').write_text('# S2 asynchronous sandbox boundary review\n\nVerdict: **NEEDS_FIX_ASYNC_WRITE_CANCELLATION** for frozen source `2f30646`. No P1 finding.\n\nThe primary native replay passed the three author test groups and 34 independent assertions. A targeted concurrent-writer probe then reproduced one P2: a second `Write(ctx)` whose 40ms deadline expired remained queued after 200ms, returning only after explicit cancellation released the first blocked writer. The final count is 36 passing and one failing independent assertions, with command exits 0 and 1 preserved.\n\nThe fix should make serialized write admission context/process-aware while preserving frame atomicity and blocked in-flight cancellation. Raw reproduction: `queued.stdout.jsonl`, `native/queued-write.json`, and `queued_write_test.go`.\n\n'+ '\n'.join('- '+x for x in limits)+'\n',encoding='utf-8')
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='index.json']
write(OUT/'index.json',{'source_revision':audit['source_revision'],'files':files})
for row in files:assert sha(OUT/row['path'])==row['sha256']
print(json.dumps({'review_sha256':sha(OUT/'review.json'),'index_sha256':sha(OUT/'index.json'),'indexed_files':len(files),'verdict':review['verdict']}))
