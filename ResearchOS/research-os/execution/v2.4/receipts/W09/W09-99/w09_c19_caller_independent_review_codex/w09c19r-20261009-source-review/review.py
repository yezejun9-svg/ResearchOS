import sys
sys.dont_write_bytecode=True
import ast,copy,difflib,hashlib,json,os,re,types
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parent.parent;R=B.parents[4]
C=B/'w09_c19_caller_source_codex/w09c19-1a11f08'
BASE=R/'execution/v2.4/receipts/W05/W05-99/history20_five_parent_caller_independent_review_codex/h20v-20261009-source-review'
checks=[];inputs={};canonical=set()
def ck(name,value):checks.append({'name':name,'pass':bool(value)})
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def verify(v):
 e={'path':str(Path(v['path']).resolve()),'sha256':v['sha256'].removeprefix('sha256:'),'bytes':v['bytes']}
 ck('pin:'+e['path'],pin(e['path'])==e);inputs[e['path'].casefold()]=e
 return e
def fixed(p,h,b):return verify({'path':str(p),'sha256':h,'bytes':b})
def add(p):return verify(pin(p))
def read(p):return json.loads(Path(p).read_bytes())
def save(name,x):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
fixed(C/'handoff.json','93b284118a5f099fc9281930416cdd2671666db409b17791bec16473c06aa72e',2931)
fixed(C/'manifest.json','85f0727b213249252fdaa19d3e183f480860b97cbb691350139ce0eb7503e2d8',8040)
h=read(C/'handoff.json');m=read(C/'manifest.json')
ck('27-members',m['member_count']==len(m['members'])==27)
for v in m['members']:verify(v)
for v in h.values():
 if isinstance(v,dict) and {'path','sha256','bytes'}<=set(v):verify(v)
choice=read(h['choice_ref']['path']);summary=read(h['summary_ref']['path']);contract=read(h['calling_contract_ref']['path'])
for v in choice['original_input_refs']+choice['base_driver_refs']+choice['review_refs']:verify(v)
review=read(choice['review_refs'][0]['path'])
ck('original-six-source-review-reused',review['decision']=='READY_SOURCE_PREPARATION_ONLY' and review['code_review_verdict']=='APPROVE_SOURCE_ONLY' and review['author'] is False and not review['requested_changes'] and not review['critical_findings'] and not review['important_findings'])
oldselected={str(Path(v['path']).resolve()):verify(v) for v in review['selected_source_refs']}
ck('exact-six-approved-refset',len(choice['sources'])==6 and {str(Path(v['path']).resolve()) for v in choice['sources'].values()}==set(oldselected))
for relative,v in choice['sources'].items():
 verify(v);copyref=summary['exact_source_copies'][relative];verify(copyref)
 ck('six-byte-copy:'+relative,Path(v['path']).read_bytes()==Path(copyref['path']).read_bytes() and pin(v['path'])['sha256']==oldselected[str(Path(v['path']).resolve())]['sha256'])
nexttask=read(choice['original_input_refs'][0]['path'])
ck('C19-reader-scope-no-W05dependency',nexttask['decision']=='READY_TO_ASSIGN_SOURCE_COMPOSITION_AND_BOUNDED_PRODUCER_PREPARATION' and nexttask['execution_grant'] is False and nexttask['does_not_depend_on']=='W05-99')
ck('reader-exact-six-map',{x['target']:verify(x['candidate_ref']) for x in nexttask['source_files']}=={k:verify(v) for k,v in choice['sources'].items()})
fixed(BASE/'HDF.json','e808790820ae697a5955483a7a9ba6600568ec27329859ce9efcd4c7fe9d207e',3530)
fixed(BASE/'MF.json','0263f752fa68b7017bae2cb9b0b91d4107ce00d878b359bd490ec3790e5d9fda',2921)
# Reuse prior caller review without re-running its 978-input audit.
baseh=read(BASE/'HDF.json')
ck('base-independent-source-review-present',bool(baseh))
for v in choice['original_input_refs']:
 if Path(v['path']).parent==R/'execution/v2.4':
  canonical.add(str(Path(v['path']).resolve()).casefold())
ck('four-live-canonical',len(canonical)==4 and read(choice['checkpoint_ref']['path'])['revision']==364)
ck('fixed-paths-contract',choice['fixed_paths']==contract['fixed_paths'] and len(contract['fixed_paths'])==5)
for name,p in contract['fixed_paths'].items():ck('fresh-absent:'+name,not os.path.lexists(p))
ck('five-independent-new-paths',len({str(Path(p).resolve()).casefold() for p in contract['fixed_paths'].values()})==5)
ck('checkpoint-contract-binding',contract['required_current_checkpoint']==choice['checkpoint_ref']==h['checkpoint_ref'] and contract['required_revision']==choice['checkpoint_revision']==364)
ck('contract-no-execution-grant',contract['run_once'] and not contract['automatic_retry'] and not contract['execution_grant'] and choice['execution_grant'] is False and h['execution_grant'] is False)
prep=Path(h['prepare_caller_ref']['path']).read_text(encoding='utf-8')
producer=Path(h['producer_caller_ref']['path']).read_text(encoding='utf-8')
oldprep=Path(choice['base_driver_refs'][0]['path']).read_text(encoding='utf-8')
oldprod=Path(choice['base_driver_refs'][1]['path']).read_text(encoding='utf-8')
trees=[ast.parse(x) for x in (prep,producer,oldprep,oldprod)]
def literal_paths(tree):
 out={}
 for node in tree.body:
  if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='Path' and len(node.value.args)==1 and isinstance(node.value.args[0],ast.Constant):
   for target in node.targets:
    if isinstance(target,ast.Name):out[target.id]=str(Path(node.value.args[0].value).resolve())
 return out
pp,cp=literal_paths(trees[0]),literal_paths(trees[1])
for variable,label in [('T','candidate'),('O','isolation_receipt'),('scratch','prepare_environment')]:ck('prepare-fixed-path:'+label,pp[variable]==str(Path(contract['fixed_paths'][label]).resolve()))
for variable,label in [('T','candidate'),('O','producer_receipt'),('ISO','isolation_receipt'),('scratch','producer_environment')]:ck('producer-fixed-path:'+label,cp[variable]==str(Path(contract['fixed_paths'][label]).resolve()))
dump=lambda x:ast.dump(x,include_attributes=False)
functions=lambda t:{x.name:x for x in t.body if isinstance(x,ast.FunctionDef)}
pf,cf,opf,ocf=map(functions,trees)
for name in pf:ck('prepare-function-preserved:'+name,dump(pf[name])==dump(opf[name]))
for name in ('pin','verify','save','module','members','unique'):ck('producer-utility-preserved:'+name,dump(cf[name])==dump(ocf[name]))
oldtry=next(n for n in reversed(trees[2].body) if isinstance(n,ast.Try))
newtry=next(n for n in reversed(trees[0].body) if isinstance(n,ast.Try))
ck('prepare-owned-six-try-and-finally-preserved',dump(oldtry)==dump(newtry))
ptry=next(n for n in reversed(trees[1].body) if isinstance(n,ast.Try))
original_final=next(n for n in reversed(trees[3].body) if isinstance(n,ast.Try)).finalbody
newfinal=copy.deepcopy(original_final)
# Only remove the binary guard no longer used by this Python producer wrapper.
for n in ast.walk(ast.Module(body=newfinal,type_ignores=[])):
 if isinstance(n,ast.For) and isinstance(n.iter,ast.Tuple):
  n.iter.elts=[v for v in n.iter.elts if not (isinstance(v,ast.Tuple) and any(isinstance(a,ast.Name) and a.id=='binary_guard' for a in v.elts))]
ck('producer-finally-exact-minus-unused-binary-guard',[dump(n) for n in ptry.finalbody]==[dump(n) for n in newfinal])
delta=read(summary['delta_ref']['path']);deltas=[]
for index,entry in enumerate(delta):
 old=Path(entry['original_ref']['path']).read_bytes();new=Path(entry['candidate_ref']['path']).read_bytes();verify(entry['original_ref']);verify(entry['candidate_ref'])
 ol=old.decode('utf-8').splitlines(keepends=True);nl=new.decode('utf-8').splitlines(keepends=True)
 x=y=0
 for op in entry['opcodes']:
  ck('contiguous-delta:'+str(index)+':'+str(x),op['old_start']==x and op['new_start']==y)
  ck('delta-source-slices:'+str(index)+':'+str(x),op['old_lines']==ol[op['old_start']:op['old_end']] and op['new_lines']==nl[op['new_start']:op['new_end']])
  if op['op']=='equal':ck('equal-delta:'+str(index)+':'+str(x),op['old_lines']==op['new_lines'])
  x=op['old_end'];y=op['new_end']
 ck('complete-delta-ends:'+str(index),x==len(ol) and y==len(nl))
 ck('full-byte-forward-inverse:'+str(index),''.join(a for op in entry['opcodes'] for a in op['old_lines']).encode()==old and ''.join(a for op in entry['opcodes'] for a in op['new_lines']).encode()==new)
 independent=list(difflib.SequenceMatcher(a=ol,b=nl,autojunk=False).get_opcodes())
 ck('independent-diff-identical:'+str(index),independent==[(o['op'],o['old_start'],o['old_end'],o['new_start'],o['new_end']) for o in entry['opcodes']])
 deltas.append({'original_ref':entry['original_ref'],'candidate_ref':entry['candidate_ref'],'changed_blocks':sum(x['op']!='equal' for x in entry['opcodes']),'complete_byte_inverse':True})
save('independent-delta.json',deltas)
ck('prepare-fixed-checkpoint-and-parent-create','checkpoint_revision==364' in prep and 'checkpoint_bytes==4237636' in prep and 'assert not O.exists();O.mkdir(parents=True)' in prep)
ck('producer-current-isolation-dynamic-ref','isolation_ref=verify({"path":str(ISO/"isolation.ready.json"),"sha256":sys.argv[6],"bytes":int(sys.argv[7])})' in producer)
ck('six-copy-no-gofmt','path.write_bytes(input_guard.get_buffer(ref["path"]))' in producer and 'gofmt' not in producer and 'str(fmt)' not in producer)
ck('one-list-one-producer',producer.count('success("compiler-input-list"')==1 and producer.count('result=invoke("w09-c19-producer"')==1)
ck('full-fields-and-compiler-guard-before-producer',all('"'+f+'"' in producer for f in ('GoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CgoFiles','SysoFiles')) and producer.index('compiler_guard.acquire(compiler_refs)')<producer.index('result=invoke("w09-c19-producer"'))
ck('no-extra-test-binary-native-harness','test2json' not in producer and 'researchos_native_recovery_harness' not in producer and '"test","-c"' not in producer)
ck('bounded-list-and-producer','"./internal/domain"],240)' in producer and 'str(T/"ops/ci/retrieval.py")],420,T)' in producer)
ck('frozen-fixture-environment',all(v in producer for v in ('"RESEARCHOS_TASK_ID":"W09"','"RESEARCHOS_CHECK_ID":""','"RESEARCHOS_CASE_ID":"C19"','"RESEARCHOS_RETRIEVAL_MODE":"fixture"','"GOTOOLCHAIN":"local"','"GOPROXY":"off"','"GOSUMDB":"off"','"GOWORK":"off"','"GOENV":"off"')))
ck('invoke-exception-receipt-finally',bool(cf['invoke'].body) and any(isinstance(n,ast.Try) and n.finalbody for n in cf['invoke'].body))
ck('job-closure-before-return',all(x in ast.unparse(cf['invoke']) for x in ('active_processes_last_observed','handles_closed','primary_exit_confirmed','job_idle_confirmed','assigned_before_resume')))
ck('timeout-rejected-after-archive',producer.index('native-packet.public-index.json')<producer.index('assert result["actual_exit"]==0 and not result["timed_out"] and report'))
ck('unique-new-run-not-latest','assert not base.exists()' in producer and 'assert len(created)==1' in producer and 'run-[0-9a-f]{32}' in producer and 'latest' not in ''.join(l for l in producer.splitlines() if not l.lstrip().startswith('#')))
ck('archive-raw-exact-pins','with dest.open("xb") as stream:stream.write(path.read_bytes())' in producer and '(a["sha256"],a["bytes"])==(b["sha256"],b["bytes"])' in producer)
ck('emitted-run-binding','(T/emitted["report_reference"]).resolve()==report_path' in producer and '(T/emitted["tool_run_reference"]).resolve()==tool_path' in producer)
ck('failure-no-retry','except BaseException as error:' in producer and 'FAILED_C19_LIST_OR_SINGLE_PRODUCER_CLOSED' in producer and 'retry' not in producer)
ck('report-native-five-not-formal-three',choice['expected_native_ids']==['C19-01','C19-02','C19-03','C19-04','C19-05'] and choice['expected_formal_ids']==['C19-01','C19-02','C19-03'] and 'report["assertions"]==5' in producer and 'report["formal_case_accepted_delta"]==0' in producer)
ck('formal-consumers-unbound',choice['formal_consumers']=='NOT_RUN_REGISTRY_UNBOUND' and 'formal_consumers="NOT_RUN_REGISTRY_UNBOUND"' in producer and h['formal_consumer_registry']=='UNBOUND')
ck('argv-preparation',contract['preparation_argv'][6]==h['prepare_caller_ref']['path'] and contract['preparation_argv'][7:]==[h['checkpoint_ref']['sha256'],str(h['checkpoint_ref']['bytes']),'364'])
ck('argv-producer',contract['producer_caller_argv_template'][6]==h['producer_caller_ref']['path'] and contract['producer_caller_argv_template'][7:12]==[h['choice_ref']['sha256'],str(h['choice_ref']['bytes']),h['checkpoint_ref']['sha256'],str(h['checkpoint_ref']['bytes']),'364'])
# Analyze actual producer order, router comparison and closure reconstruction.
retrieval=Path(choice['sources']['ops/ci/retrieval.py']['path']).read_text(encoding='utf-8')
router=Path(choice['sources']['ops/ci/w09_formal_router.py']['path']).read_text(encoding='utf-8')
closure=Path(choice['sources']['ops/ci/w09_evidence_closure.py']['path']).read_text(encoding='utf-8')
rt=ast.parse(retrieval);routertree=ast.parse(router);ct=ast.parse(closure)
testmap=ast.literal_eval(next(n.value for n in rt.body if isinstance(n,ast.Assign) and any(isinstance(a,ast.Name) and a.id=='TESTS' for a in n.targets)))
case=['TestW09C19ExplicitOriginAndUnknown','TestW09C19ChainInvalidation']
selected=[name for name in testmap if name in case]
ck('actual-producer-order',selected==choice['selected_tests']==['TestW09C19ChainInvalidation','TestW09C19ExplicitOriginAndUnknown'])
ck('producer-select-filter-order-preserved','selected = GROUPS[check] if check else list(TESTS)' in retrieval and 'selected = [name for name in selected if name in CASES[case]]' in retrieval)
ck('router-set-compare-no-reorder','sorted(selected) != sorted(SELECTED[route])' in router and 'verify_native(ROOT, source, report, expected, selected)' in router)
ck('closure-source-order-reconstruction','"^(?:" + "|".join(selected) + ")$"' in closure)
author=read(h['source_controls_ref']['path'])
ck('author53-controls-source-only',author['check_count']==len(author['checks'])==53 and all(x['status']=='PASS' for x in author['checks']) and author['synthetic_control_only'] and not author['native_executed'] and not author['formal_consumer_main_executed'] and not author['formal_acceptance'])
order=author['consumer_order_controls']
ck('both-consumers-same-synthetic-input',len(order)==2 and order[0]==order[1] and order[0]['selected_tests']==selected)
# Independent tiny AST-only in-memory bridge check; no module/main/real consumer.
ns={'json':json,'ROOT':'INDEPENDENT_SYNTHETIC_ROOT'}
for node in routertree.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'NATIVE','SOURCE_SCOPE','SELECTED'}:
  ns[node.targets[0].id]=ast.literal_eval(node.value)
fn=functions(routertree)['_native_exact'];exec(compile(ast.Module(body=[fn],type_ignores=[]),'<router-function-only>','exec'),ns)
vf=functions(ct)['verify_native'];argvnodes=[n for n in vf.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('packages','argv') for t in n.targets)]
report={'status':'PASS','task_id':'W09','check_id':None,'case_id':'C19','scope':'FIXTURE_IMPLEMENTED_SERVICE','exit_code':0,'timed_out':False,'assertion_ids':choice['expected_native_ids'],'expected_assertion_ids':choice['expected_native_ids'],'assertions':5,'selected_tests':selected,'passed_tests':sorted(selected),'run_id':'1'*32,'go_executable':{'path':'SYNTHETIC_GO'},'raw_evidence_references':['run-'+('1'*32)+'/go-test.stdout.jsonl','run-'+('1'*32)+'/go-test.stderr.txt']}
report['actual_invocation']=['SYNTHETIC_GO','test','-count=1','-json','-run','^(?:'+'|'.join(selected)+')$','./internal/domain']
report['assertion_results']=[{'assertion_id':x,'status':'PASS','raw_evidence_reference':report['raw_evidence_references'][0]} for x in choice['expected_native_ids']]
source=copy.deepcopy(report);source['report_reference']='run-'+('1'*32)+'/report.json'
class Memory:
 def read_bytes(self):return json.dumps(report).encode()
ns['_pin']=lambda x:{'synthetic_ref':x};ns['_inside_repo']=lambda x:Memory();seen=[]
def intercept(root,source,report,expected,selected):
 env={'report':report,'selected':selected}
 exec(compile(ast.Module(body=argvnodes,type_ignores=[]),'<closure-argv-statements-only>','exec'),env)
 ck('independent-consumer-argv',env['argv']==source['actual_invocation'])
 seen.append({'run':source['run_id'],'ref':source['report_reference'],'selected':selected,'argv':env['argv']})
 return {'synthetic_only':True}
ns['verify_native']=intercept
for route in ('test.research.fixture','test.retrieval'):ns['_native_exact'](source,(route,'W09','','C19'))
ck('independent-two-consumers-same-run',len(seen)==2 and seen[0]==seen[1])
save('order-bridge-control.json',{'synthetic_only':True,'formal_consumer_main_executed':False,'seen':seen,'native_or_producer_executed':False})
# Candidate guard is read-only. Exclude canonical files already held by Root.
gp=R/'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
gm=types.ModuleType('w09caller_independent_source_guard');gm.__file__=str(gp);sys.modules[gm.__name__]=gm;exec(compile(gp.read_bytes(),str(gp),'exec'),gm.__dict__)
add(__file__);add(sys.executable)
for mod in list(sys.modules.values()):
 for k in ('__file__','__cached__'):
  p=getattr(mod,k,None)
  if p and Path(p).is_file():add(p)
guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
try:
 guard.acquire([v for k,v in inputs.items() if k not in canonical])
 for v in inputs.values():ck('post-review-unchanged:'+v['path'],pin(v['path'])==v)
 for name,p in contract['fixed_paths'].items():ck('post-review-fresh-absent:'+name,not os.path.lexists(p))
finally:
 cleanup=guard.close();save('sourceguard.final.json',cleanup)
ck('independent-guard-closed',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
save('input-pins.json',list(inputs.values()))
save('checks.json',{'checks':checks,'count':len(checks),'inputs':len(inputs),'all_pass':all(c['pass'] for c in checks),'failed':[c for c in checks if not c['pass']]})
print(json.dumps({'checks':len(checks),'input_count':len(inputs),'failed':[c for c in checks if not c['pass']],'guard_closed':cleanup['closed'],'actual_product_Git_Go_SQL_native_API_private_model':False},ensure_ascii=True))
sys.exit(0 if all(c['pass'] for c in checks) else 1)

