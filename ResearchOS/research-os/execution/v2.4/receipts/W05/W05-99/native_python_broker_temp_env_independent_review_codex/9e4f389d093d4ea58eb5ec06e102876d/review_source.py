import sys
sys.dont_write_bytecode=True
import json,hashlib,ast,copy,importlib.util,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
B=R/'execution/v2.4/receipts/W05/W05-99'
P=B/'native_python_broker_temp_env_revision_codex/7bc2467624af477a8d55e0595ec4a7c2'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
checks=[];guard=None
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def norm(r):return {'path':str(Path(r['path'])),'sha256':r['sha256'].removeprefix('sha256:'),'bytes':r['bytes']}
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def check(n,v,details=None):checks.append({'name':n,'passed':bool(v),'details':details})
def main():
 global guard
 h=json.loads((P/'HDF.json').read_bytes());m=json.loads((P/'MF.json').read_bytes())
 bm=json.loads(Path(h['base_MF_ref']['path']).read_bytes())
 cl=json.loads((P/'source-guard-closure.json').read_bytes())
 refs=[pin(p) for p in sorted(P.rglob('*')) if p.is_file()]
 refs.extend(norm(r) for r in bm['members'].values())
 refs.extend(norm(h[k]) for k in ['base_ref','base_HDF_ref','base_MF_ref'])
 refs.extend(norm(pair['source_ref']) for pair in cl['copied_input_source_and_snapshot_refs_reverified'])
 refs.extend([pin(G),pin(Path(__file__))])
 unique={}
 for r in refs:
  if r['path'] in unique:assert unique[r['path']]==r
  unique[r['path']]=r
 refs=list(unique.values())
 canon=[R/'execution/v2.4'/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']]
 before=[pin(p) for p in canon]
 assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85' and pin(G)['bytes']==11404
 spec=importlib.util.spec_from_file_location('independent_broker_source_read_guard',str(G));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 guard=mod.SourceReadGuard();guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(Path(p)))
 def read(p):return json.loads(raw(p))
 def verify(r):return hashlib.sha256(raw(r['path'])).hexdigest()==r['sha256'].removeprefix('sha256:') and len(raw(r['path']))==r['bytes']
 save('input-pins.json',refs)
 anchors=[('HDF.json','ed0f388870aef974f9577e6d5146637d5a1a77ce6b22c57e989227654de05824',6761),('MF.json','deab5d3bb0fc512c37808a4dcd9b66d370dcd0c1ae14b84e1949fcfdb915ebdc',9803),('root_only_native_broker.py','70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c',8562),('broker_temp_environment_boundary_test.py','0b5f78f27a5a52c74f438b954d40d561c1149b85a13bd8650964b635cf264963',7677)]
 for n,sha,size in anchors:check('fixed-anchor:'+n,hashlib.sha256(raw(P/n)).hexdigest()==sha and len(raw(P/n))==size)
 check('MF-is-list-25',isinstance(m['members'],list) and len(m['members'])==25)
 check('MF-exclusions-exact',m['exclusions_exact_relative_paths']==['MF.json','postseal-tool-io.json'])
 check('MF-complete-recursive-inventory',set(x['relative_path'] for x in m['members'])=={p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()}-{'MF.json','postseal-tool-io.json'})
 for r in m['members']:check('MF-member:'+r['relative_path'],Path(r['path'])==P/r['relative_path'] and verify(r))
 check('base-MF-shape14',isinstance(bm['members'],dict) and len(bm['members'])==14)
 for n,r in bm['members'].items():check('base-MF-member:'+n,verify(r))
 for pair in cl['copied_input_source_and_snapshot_refs_reverified']:
  check('source-snapshot:'+Path(pair['snapshot_ref']['path']).relative_to(P).as_posix(),verify(pair['source_ref']) and verify(pair['snapshot_ref']) and raw(pair['source_ref']['path'])==raw(pair['snapshot_ref']['path']))
 check('author-closure-is-explicit-static-not-runtime',cl['actual_Root_retained_guard']=='NOT_RUN; Root requires full fresh runtime public resource closure' and cl['old_Sources_Main_canonical_Tstar_writes']==0)
 base=raw(h['base_ref']['path']);cand=raw(P/'root_only_native_broker.py')
 inverse=read(P/'exact-inverse-edits.json')
 old=inverse['old_single_guard'].encode();new=inverse['new_single_guard'].encode();insert=inverse['inserted_helper_text'].encode()
 check('single-exact-edit-counts',cand.count(new)==1 and cand.count(insert)==1 and base.count(old)==1)
 recovered=cand.replace(insert,b'',1).replace(new,old,1)
 check('inverse-restores-all6201-basebytes',recovered==base and len(recovered)==6201)
 with (O/'recovered-base.py').open('xb') as f:f.write(recovered)
 bt=ast.parse(base);ct=ast.parse(cand);rt=ast.parse(recovered)
 check('recovered-entire-AST-equals-base',ast.dump(rt)==ast.dump(bt))
 bd={x.name:x for x in bt.body if isinstance(x,ast.FunctionDef)};cd={x.name:x for x in ct.body if isinstance(x,ast.FunctionDef)}
 check('only-added-definition',set(cd)-set(bd)=={'require_public_environment'} and set(bd)-set(cd)==set())
 for n in ['raw_pin','require_pin','write_new','read_private_pipe']:
  check('unchanged-definition:'+n,ast.dump(bd[n])==ast.dump(cd[n]) and ast.get_source_segment(base.decode(),bd[n])==ast.get_source_segment(cand.decode(),cd[n]))
 repaired_main=copy.deepcopy(cd['main'])
 target=repaired_main.body[2].body
 old_guard=next(x for x in bd['main'].body[2].body if isinstance(x,ast.If) and ast.unparse(x.test).startswith("set(request['Environment'])"))
 calls=[i for i,x in enumerate(target) if isinstance(x,ast.Expr) and isinstance(x.value,ast.Call) and isinstance(x.value.func,ast.Name) and x.value.func.id=='require_public_environment']
 check('one-main-environment-call',len(calls)==1)
 if len(calls)==1:target[calls[0]]=copy.deepcopy(old_guard)
 check('all-other-main-AST-unchanged',ast.dump(repaired_main)==ast.dump(bd['main']))
 helper=cd['require_public_environment'];hs=ast.get_source_segment(cand.decode(),helper)
 check('exact-four-key-and-dict-gate',ast.literal_eval(helper.body[0].value)=={'SystemRoot','WINDIR','TEMP','TMP'} and 'not isinstance(env, dict) or set(env) != expected' in hs)
 check('strict-public-string-values',all(x in hs for x in ['not isinstance(value, str)','not value.strip()','"\\0" in value']))
 check('TEMP-TMP-literal-equality','if env["TEMP"] != env["TMP"]:' in hs)
 check('fixed-local-and-trial',str(R/'.local').replace('\\','/') in hs and 'mu-sdk-isolated-project-ed84838046934329a76733a005c9b162' in hs)
 check('absolute-existing-resolved-casefold-directory',all(x in hs for x in ['not path.is_absolute()','str(path.resolve()).casefold() != str(path).casefold()','not path.is_dir()']))
 check('component-aware-casefold-containment','os.path.commonpath([parent_key, child_key]) == parent_key' in hs and 'str(parent).casefold(), str(child).casefold()' in hs)
 check('strict-local-child-both-checks','declared == local or not contains(local, declared)' in hs and 'root == local or not contains(local, root)' in hs)
 check('trial-lexical-before-directory-metadata',hs.index('if contains(trial, declared) or contains(declared, trial):')<hs.index('local = directory(str(local))') and 'contains(physical_trial, root) or contains(root, physical_trial)' in hs)
 check('system-overlap-both-directions','for name in ("SystemRoot", "WINDIR"):' in hs and 'contains(system, root) or contains(root, system)' in hs)
 helper_calls=sorted({ast.unparse(x.func) for x in ast.walk(helper) if isinstance(x,ast.Call)})
 allowed={'isinstance','set','any','ValueError','str','Path','contains','directory','os.path.commonpath','os.path.normpath','env.values','value.strip','path.is_absolute','path.resolve','path.is_dir','declared.is_absolute','str(parent).casefold','str(child).casefold','str(path.resolve()).casefold','str(path).casefold'}
 check('helper-only-directory-metadata-and-pure-validation',set(helper_calls)<=allowed,helper_calls)
 check('no-environment-inheritance-added','os.environ' not in hs)
 main_src=ast.get_source_segment(cand.decode(),cd['main'])
 order=[main_src.index(x) for x in ['require_public_environment(request["Environment"])','output.mkdir(', 'spec = importlib.util.spec_from_file_location','spec.loader.exec_module(helper)','private_input = read_private_pipe()','result = helper.run_owned_private_stdin(']]
 check('all-boundaries-before-main-side-effects',order==sorted(order),{'guard':131,'mkdir':134,'helper_import':137,'private_read':138,'child':140})
 tests_raw=raw(P/'broker_temp_environment_boundary_test.py');tt=ast.parse(tests_raw)
 cls=next(x for x in tt.body if isinstance(x,ast.ClassDef) and x.name=='PublicEnvironmentBoundaryTests')
 tests=[x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name.startswith('test_')]
 names=[x.name for x in tests];matrix=read(P/'boundary-matrix.json');static=read(P/'static-evidence.json');prereq=read(P/'root-actual-public-prerequisites.json')
 check('17-test-methods-exact-source-matrix',len(tests)==17 and names==static['boundary_test_names'] and names==[x['test_name'] for x in matrix['cases']])
 check('all-boundaries-NOT_RUN',matrix['actual']==static['boundary_actual']==h['all_boundary_actual']=='NOT_RUN' and all(x['actual']=='NOT_RUN' for x in matrix['cases']) and prereq['Source_units']['actual']==prereq['native_runtime']['actual']=='NOT_RUN')
 check('old-two-key-rejection-test-present','test_old_two_key_request_is_rejected' in names)
 check('test-source-never-calls-native-private-helper',all(x not in tests_raw.decode() for x in ['BROKER.main(', 'read_private_pipe(', 'run_owned_private_stdin(', 'subprocess.', 'sqlite3.']))
 check('test-import-pin-before-import',tests_raw.index(b'hashlib.sha256(path.read_bytes())')<tests_raw.index(b'spec.loader.exec_module(module)'))
 check('Root-runtime-RawPin-fixed',norm(prereq['native_runtime']['BrokerSource_RawPin_required'])==pin(P/'root_only_native_broker.py'))
 check('failure868-byte-preserved',verify(h['failure868_original_and_snapshot_refs']['source_ref']) and raw(h['failure868_original_and_snapshot_refs']['source_ref']['path'])==raw(h['failure868_original_and_snapshot_refs']['snapshot_ref']['path']))
 after=[pin(p) for p in canon];save('canonical-short-pins.json',{'before':before,'after':after,'unchanged':before==after,'canonical_held':False,'concurrent_Root_updates_permitted':True})
 # Root is the sole canonical writer and may serialize an update during this Source review.
 check('canonical-never-guarded',not any(Path(r['path']) in canon for r in refs))
 cleanup=guard.close();save('guard-closure.json',cleanup)
 check('reviewer-guard-closed',cleanup['verification']=='PASSED' and cleanup['closed'] and cleanup['retained_handles_count']==0 and cleanup['failure'] is None and cleanup['errors']==[] and all(x['closed'] and x['verified'] and x['final_path_match'] for x in cleanup['entries']))
 result={'schema':'researchos.independent-broker-temp-env-source-check.v1','authority':'NONE','formal_acceptance':False,'decision':'SOURCE_STATIC_CHECKS_PASSED_PENDING_SEMANTIC_REVIEW' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','checks':checks,'guarded_input_count':len(refs),'candidate_executed':False,'candidate_or_boundary_imported':False,'boundary_actual':'NOT_RUN','Root_actual_runtime_guard':'NOT_RUN','native_positive_Owner_nine_business_formal_accepted':False,'new_mechanical_errors':0,'history_reset':False,'stop':True}
 save('source-check.json',result)
 print(json.dumps({'decision':result['decision'],'passed':sum(x['passed'] for x in checks),'total':len(checks),'failed':[x for x in checks if not x['passed']],'guarded_input_count':len(refs),'closed':cleanup['closed'],'canonical_short_pins_unchanged':before==after},ensure_ascii=False))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if guard is not None:
  cleanup=guard.close()
  if not (O/'guard-closure.json').exists():save('guard-closure.json',cleanup)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)

