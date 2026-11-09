import ast,hashlib,json,difflib,os
from pathlib import Path
from datetime import datetime,timezone
R=Path('D:/作品集/ResearchOS/research-os');H=Path(__file__).resolve().parent
W=R/'.local/worktrees/codex-w0599-session-list-proof-r312';P=W/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V=P/'v3-boundary-preparation-cafb9c77a62a4904bb2027ea866ff947';OLD=P/'v2-preparation-48a141cf916944aabe60ea42f6bd6dbe'
def need(x,m):
 if not x:raise RuntimeError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(f):
 b=f.read_bytes();return {'path':f.relative_to(R).as_posix(),'sha256':sha(b),'bytes':len(b)}
def check(x):
 f=Path(x['path']);f=f if f.is_absolute() else R/f;b=f.read_bytes();need(sha(b)==x['sha256'] and len(b)==x['bytes'],'pin '+str(f));return ref(f)
def save(n,x):
 with (H/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
pins={'execute.py':'ad5a3513eca16c31ae4a4c72b054aabcaf7069e698aac77cc12901ad225bb8ea','launch.py':'bfeaa214fbc061ac30ed6b9ec0a580ad4337873e05fc101ff5fbc5af6dfb8f9e','static_audit.json':'e415084c51f000f2f823dfbf336c4dcb382387252266874f4d13cb52a90ac33e','manifest.json':'39cdfc243462449f271bc8c1599449142c28431367a377cdfa0d06549e1f27b5','handoff.json':'c18ca148dbd368252b97df1ba0a330d7148a4b98ca73dba693fbb2f3c9b58c21'}
for n,h in pins.items():need(sha((V/n).read_bytes())==h,'new draft '+n)
mf=json.loads((V/'manifest.json').read_bytes());inputs=[check(x) for x in mf['files']]
a=json.loads((V/'static_audit.json').read_bytes())
for k in ['source_current','domain_current','Root_assertions_unchanged','launcher_unchanged']:inputs.append(check(a[k]))
inputs += [check(x) for x in a['old_failure_refs']]
old=(OLD/'execute.py').read_bytes();new=(V/'execute.py').read_bytes()
need(sha(old)=='b0610c0dc587dc138a5282660fe98841ab3cc41f98dc4607eadd2be9f6315782','old frozen driver')
line1=b" require(after[:newappend].replace(b'\\t\"net/url\"\\n',b'',1)==original[:before_append],'Outsideownedprefix')"
line2=b" require(after[:newappend].replace(b'\\t\"net/url\"\\n',b'',1)==original[:before_append]+b'\\n','Outsideownedprefix_or_nonexact_new_helper_separator')"
need(old.count(line1)==new.count(line2)==1,'exact changed comparison line')
reversed_bytes=new.replace(b"WORK=W/'.local/closedcopy-v3-cafb9c77a62a4904bb2027ea866ff947'",b"WORK=W/'.local/closedcopy-v2-48a141cf916944aabe60ea42f6bd6dbe'",1).replace(line2,line1,1)
need(reversed_bytes==old,'reverse only2 changes')
need((OLD/'launch.py').read_bytes()==(V/'launch.py').read_bytes(),'launcher unchanged')
need((OLD/'root_assertions.original.py').read_bytes()==(V/'root_assertions.original.py').read_bytes(),'Root assertions unchanged')
before=(V/'source.before.go').read_bytes();unformatted=(V/'source.edited.go').read_bytes();current=(V/'source.current_gofmt.go').read_bytes()
need(current==(W/'internal/api/v2_sessions_test.go').read_bytes() and sha(current)=='9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae','current source')
need(sha(before)=='e095e2be7418d4ca7bb677e33679f25e377e084bec305f538799baf8523ea9b0' and sha(unformatted)=='54abc44af9e12181a1c19a07c0f1d192bd8e295626a825d79e6d1b93d824f320','old source copies')
newmarker=b'// readonlyCopyOpen is only';oldmarker=b'func (f *sessionListFixture) closeEvidence(';importbytes=b'\t"net/url"\n'
i=current.index(newmarker);j=before.index(oldmarker)
need(current[:i].count(importbytes)==1,'single exact added import')
removed=current[:i].replace(importbytes,b'',1);prefix=before[:j]
need(removed==prefix+b'\n','exact original prefix plus1 LF')
need(len(prefix)==29784 and len(removed)==29785,'prefix actual lengths')
k=unformatted.index(newmarker);need(current==unformatted[:k]+b'\n'+unformatted[k:],'entire gofmt delta one LF')
marker=b'// Only the host binding port';body=current[current.index(marker):current.index(marker)+14633]
need(sha(body)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1','protected body')
suffix=b'func TestSessionListHTTPOriginalContextIdentity';need(current[current.index(suffix):]==before[before.index(suffix):],'original14 suffix')
failure=json.loads((OLD/'failure_origin.json').read_bytes());need(failure['actual_driver_exit']==1 and failure['error']=="RuntimeError('Outsideownedprefix')" and len(failure['invocations'])==3 and not failure['completed'] and len(failure['not_run'])==14,'actual stopped stage')
child=[]
for x in failure['invocations']:
 child.append(check(x['ref']));need(x['actual_exit']==0,'child native')
 recorded=json.loads(Path(x['ref']['path']).read_bytes());need(recorded['actual_exit']==0,'recorded child exit')
for n in ['execute.py','launch.py','root_assertions.original.py']:ast.parse((V/n).read_bytes(),filename=n)
work=W/'.local/closedcopy-v3-cafb9c77a62a4904bb2027ea866ff947';need(not os.path.lexists(work) and not (V/'started.json').exists(),'v3 not started')
inputs += [ref(OLD/'execute.py'),ref(OLD/'launch.py'),ref(V/'manifest.json'),ref(V/'handoff.json')]+child
(H/'copies').mkdir()
for ix,f in enumerate([V/n for n in ['execute.py','launch.py','static_audit.json','manifest.json','handoff.json','source.before.go','source.edited.go','source.current_gofmt.go','execute.v2-to-v3.diff','root_assertions.original.py']]+[OLD/'execute.py',OLD/'failure_origin.json']):
 with (H/'copies'/f'{ix:02d}-{f.name}').open('xb') as out:out.write(f.read_bytes())
checks=['Exact two driver edits reverse to pinned v2: fresh leaf plus original prefix+singleLF comparison. No trim/rstrip/normalization or broad byte allowance.',
 'Observed current source equals unformatted source with precisely one inserted LF immediately before new helper comment; exact single net/url import subtraction produces original29784-byteprefix+LF.',
 'Protected14633-byte body c845 and entire original14-case suffix unchanged; current9556e94 and domain7fb40 match. This does not accept production/test source.',
 'All Root assertion code, launcher, path/alias/Job/closure/caps/firststop logic unchanged by byte equality outside the two allowed edits.',
 'V2 recorded Git HEAD/status/gofmt three child exits0 followed by boundary-check driver1. No Go compilation/cases/HTTP. Old aa7b24 and18e863 are distinct retained failures, same-chain2.',
 'Future once-only v3 execution needs actual Root315 registration and followup, fresh leaf/cache/exe/compiler graph/full closure; no old-output reuse or automatic retry.']
save('audit.json',{'input_refs':inputs,'checks':checks,'exact_reverse_restores_v2':True,'single_LF_insertion_offset':k,'prefix_original_bytes':len(prefix),'prefix_current_minus_import_bytes':len(removed),'protected14633_sha256':sha(body),'original14_suffix_equal':True,'retained_failure_chain':2,'AST_only':True,'new_failures':[],'execution_calls':0})
for x in inputs:check(x)
save('review.json',{'schema':'researchos.closedcopy-harness-independent-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION','requested_changes':[],'reviewed_at':datetime.now(timezone.utc).isoformat(),'driver_ref':ref(V/'execute.py'),'launcher_ref':ref(V/'launch.py'),'author_manifest_ref':ref(V/'manifest.json'),'author_handoff_ref':ref(V/'handoff.json'),'author_audit_ref':ref(V/'static_audit.json'),'independent_audit_ref':ref(H/'audit.json'),'source_current_ref':ref(W/'internal/api/v2_sessions_test.go'),'conditions':['Only after actualCAS315 and precise Root followup; once-only new input/leaf/output.','All14/max224HTTP/fullinput/Job/firstUnexpectedStop guards retained; no automatic retry.','Preserve aa7b24 and18e863 raw/counters; source/Main/formal still unaccepted.'],'known_limitations':['Existing same-user path TOCTOU remains, no handle-relative directory guarantee.','AST and byte arithmetic do not prove runtime cases or source acceptance; future execution must bind actual post-gofmt current source and full compiler/testexe graph.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'actual_Go_SQL_Node_HTTP_MODEL_helper_execution':0,'new_failure_origins':[]})
save('manifest.json',{'files':[ref(f) for f in sorted(H.rglob('*')) if f.is_file()]})
save('handoff.json',{'review_ref':ref(H/'review.json'),'manifest_ref':ref(H/'manifest.json'),'audit_ref':ref(H/'audit.json'),'source_acceptance':False,'actual_execution':False,'new_failure_origins':[]})
print(json.dumps({n:ref(H/n) for n in ['review.json','manifest.json','handoff.json']},ensure_ascii=False,indent=2))
