from pathlib import Path
import ast,json,hashlib,datetime,difflib
R=Path('D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/codex-w0599-session-list-proof-r312'
B=W/'execution/v2.4/receipts/W05/W05-99/session_list_closedcopy_exact1_executor_codex'
V=B/'v4-encoding-preparation-0a6c023f68e849ea8fa73443dfa3b10b'
OLD=B/'v3-boundary-preparation-cafb9c77a62a4904bb2027ea866ff947'
O=Path(__file__).resolve().parent
reads={}
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p,b=None):
 p=Path(p);b=p.read_bytes() if b is None else b
 return {'path':p.relative_to(R).as_posix() if p.is_relative_to(R) else str(p),'sha256':sha(b),'bytes':len(b)}
def read(p):
 p=Path(p);b=p.read_bytes();reads[p]=b;return b
def verify(e):
 p=Path(e['path']);p=p if p.is_absolute() else R/p;b=read(p)
 assert sha(b)==e['sha256'],str(p)
 if 'bytes' in e:assert len(b)==e['bytes'],str(p)
 return b
def save(name,obj):
 b=obj if isinstance(obj,bytes) else (json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with (O/name).open('xb') as f:f.write(b)
 return ref(O/name,b)
pins={'execute.py':'e52fd10a4dbb6b3fb29850c4fae003c1e502bc629de0c11440a39a21204c8326','launch.py':'bfeaa214fbc061ac30ed6b9ec0a580ad4337873e05fc101ff5fbc5af6dfb8f9e','static_audit.json':'1c4b41dd2572277d64f97480fdfafa39f163247426a1e8057c90d2cf592b94f4','manifest.json':'3bcea5a0002096a6e5acf894035dbc5bfec9de5dd8b1a583b6d0326056c44920','handoff.json':'a31ad0c9f068ee2d5e3fb631a7d8a426c93198d348131c773b0e8e80b176c28d'}
for name,h in pins.items(): save('author-'+name,verify({'path':str(V/name),'sha256':h}))
mf=json.loads(read(V/'manifest.json'))
for e in mf['files']:verify(e)
new=read(V/'execute.py');old=read(OLD/'execute.py')
reverse=new
a=json.loads(read(V/'static_audit.json'))
for change in a['exact_diff']:
 b=change['before'].encode('utf-8');c=change['after'].encode('utf-8')
 assert reverse.count(c)==1
 reverse=reverse.replace(c,b,1)
assert reverse==old
assert read(V/'launch.py')==read(OLD/'launch.py')
assert read(V/'root_assertions.original.py')==read(OLD/'root_assertions.original.py')
for f in ('execute.py','launch.py','root_assertions.original.py'):ast.parse(read(V/f))
save('independent.diff',''.join(difflib.unified_diff(old.decode('utf-8').splitlines(True),new.decode('utf-8').splitlines(True),fromfile='v3',tofile='v4')).encode())
source=verify(a['source_current']);verify(a['domain_current'])
original=read(V/'source.before.go');marker=b'// Only the host binding port'
protected=source[source.index(marker):source.index(marker)+14633]
assert sha(protected)=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1'
assert source[:source.index(b'// readonlyCopyOpen is only')].replace(b'\t"net/url"\n',b'',1)==original[:original.index(b'func (f *sessionListFixture) closeEvidence(')]+b'\n'
assert source[source.index(b'func TestSessionListHTTPOriginalContextIdentity'):]==original[original.index(b'func TestSessionListHTTPOriginalContextIdentity'):]
for e in a['old_failure_refs']:verify(e)
failure=json.loads(read(OLD/'failure_origin.json'));report=json.loads(read(OLD/'stopped_report.v3.json'))
save('original-v3-failure.json',read(OLD/'failure_origin.json'));save('original-v3-stopped-report.json',read(OLD/'stopped_report.v3.json'))
assert failure['completed']==[] and len(failure['not_run'])==14 and len(failure['invocations'])==7
invocations=[]
for x in failure['invocations']:
 b=verify(x['ref']);i=json.loads(b)
 assert x['actual_exit']==i['actual_exit']==0
 invocations.append({'name':x['name'],'ref':ref(Path(x['ref']['path']),b),'actual_exit':i['actual_exit'],'job_cleanup':i['result']['job_cleanup']})
archives=json.loads(read(OLD/'archives.readonly-after-stop.UTF8.json'))
assert archives['count']==len(archives['files'])==353
vectors=[]
for name in ['inputs.after_Go_list.json','inputs.after_compile.json','inputs.after_failure.json']:
 b=read(OLD/name);v=json.loads(b)
 vectors.append({'ref':ref(OLD/name,b),'errors':v['errors'],'count':len(v['files'])})
assert all(not x['errors'] for x in vectors)
tree=ast.parse(new)
strict=[]
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='read_text':
  kwargs={k.arg:ast.literal_eval(k.value) for k in node.keywords}
  strict.append({'line':node.lineno,'kwargs':kwargs})
assert len([x for x in strict if x['kwargs']=={'encoding':'utf-8','errors':'strict'}])==2
assert not (V/'started.json').exists()
assert not (W/'.local/closedcopy-v4-0a6c023f68e849ea8fa73443dfa3b10b').exists()
assert all(p.read_bytes()==b for p,b in reads.items())
audit=save('audit.json',{'actual_execution':False,'manifest_entries_verified':len(mf['files']),'exact_reverse_restores_v3':True,'exact_diff':a['exact_diff'],'read_text_AST_inventory':strict,'source_original_protected14633_unchanged':True,'old14suffix_unchanged':True,'exact_prefix_plus_one_LF_unchanged':True,'launcher_Rootassertions_identical':True,'original_v3_driver_exit':failure['actual_driver_exit'],'original_product_exit_field_preserved':failure['actual_product_exit'],'v3_native_invocations':invocations,'v3_case_count':0,'v3_NOT_RUN':failure['not_run'],'old_vector_records':vectors,'after_stop_archive_record_count':353,'archive_closure_limit':'After-stop UTF8 diagnostic only; not retroactive pre-case qualification, underlying353 archives not rehashed here.','same_harness_chain_failures':3,'input_refs':[ref(p,b) for p,b in reads.items()],'before_after_read_inputs_equal':True,'new_failure_origins':[]})
review=save('review.json',{'schema':'researchos.closedcopy-harness-independent-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION','requested_changes':[],'reviewed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'driver_ref':ref(V/'execute.py'),'launcher_ref':ref(V/'launch.py'),'author_manifest_ref':ref(V/'manifest.json'),'author_handoff_ref':ref(V/'handoff.json'),'author_audit_ref':ref(V/'static_audit.json'),'independent_audit_ref':audit,'source_current_ref':ref(W/'internal/api/v2_sessions_test.go'),'conditions':['Only after actual Root CAS316 and precise followup; once-only fresh WORK/cache/exe/fixtures/output.','Decode only the two Go-generated text consumers as strictUTF8; no lossy fallback or path normalization.','Keep original14 assertions/percase16HTTP/total224/full input graph/Job/firstUnexpectedStop unchanged.','Retain aa7b24,18e863,30a0d4 original failures and case0 state.','Any new prerequisite or encoding failure stops; no automatic repair/retry.'],'known_limitations':['Same-user path-validation TOCTOU remains.','AST and byte-diff checks are not actual case or source acceptance.','Actual new compiler archives/testexe and complete runtime closure must be frozen before first futurecase.'],'source_acceptance':False,'Main_integration_authorized':False,'formal_increment':0,'actual_Go_SQL_Node_HTTP_MODEL_helper_execution':0,'new_failure_origins':[]})
manifest=save('manifest.json',{'entries':[ref(p) for p in sorted(O.iterdir()) if p.is_file()],'self_excluded':True})
handoff=save('handoff.json',{'decision':'TARGETED_HARNESS_REVISION_REVIEWED_FOR_ONCE_ONLY_NEW_INPUT_EXECUTION','review_ref':review,'manifest_ref':manifest,'actual_execution':False,'source_acceptance':False,'formal_increment':0,'new_failure_origins':[]})
print(json.dumps({'review':review,'manifest':manifest,'handoff':handoff},ensure_ascii=True))
