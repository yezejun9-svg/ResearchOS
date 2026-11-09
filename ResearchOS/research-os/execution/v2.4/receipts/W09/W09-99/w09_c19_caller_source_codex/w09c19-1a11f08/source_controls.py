import ast,copy,difflib,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
C=json.loads((N/'source.integration.choice.json').read_bytes())
checks=[]
def check(label,value):
 assert value,label
 checks.append(dict(label=label,status='PASS'))
def pin(p):
 p=Path(p);raw=p.read_bytes();return dict(path=str(p.resolve()),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def js(name,value):
 with (N/name).open('xb') as stream:stream.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
initial={ref['path']:Path(ref['path']).read_bytes() for ref in C['original_input_refs']}
for ref in C['original_input_refs']:
 actual=pin(ref['path']);check('original:'+Path(ref['path']).name,actual['sha256']==ref['sha256'] and actual['bytes']==ref['bytes'])
for relative,ref in C['sources'].items():
 actual=pin(ref['path']);check('exact-v6:'+relative,(actual['sha256'],actual['bytes'])==(ref['sha256'],ref['bytes']))
check('exact-six-count',len(C['sources'])==6)
prep=(N/'prepare_w09_c19.actual_owned.py').read_text(encoding='utf-8')
caller=(N/'run_w09_c19.actual_owned.py').read_text(encoding='utf-8')
pa,ca=ast.parse(prep),ast.parse(caller)
check('both-callers-AST-valid',True)
check('fresh-receipt-parent-created-by-caller','assert not O.exists();O.mkdir(parents=True)' in prep)
check('CP364-explicit-three-parameters','checkpoint_sha,checkpoint_bytes,checkpoint_revision=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])' in prep and 'checkpoint_revision==364' in prep and 'checkpoint_revision==364' in caller)
check('fixed-fresh-paths',all(not Path(p).exists() for p in C['fixed_paths'].values()))
check('single-producer-call',caller.count('result=invoke("w09-c19-producer"')==1)
check('owned-go-list-no-test-run',caller.count('success("compiler-input-list"')==1 and '"list","-test","-deps","-compiled","-json","./internal/domain"' in caller)
check('no-gofmt-no-binary-test-extra',not any(x in caller for x in ('str(fmt)','test2json','tagged-test-binary','researchos_native_recovery_harness','"test","-c"')))
check('six-source-copy-exact','path.write_bytes(input_guard.get_buffer(ref["path"]))' in caller)
check('compiler-guard-before-producer',caller.index('compiler_guard.acquire(compiler_refs)')<caller.index('result=invoke("w09-c19-producer"'))
check('full-compiler-fields',all('"'+x+'"' in caller for x in ('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')))
check('fixture-scope-env',all(x in caller for x in ('"RESEARCHOS_TASK_ID":"W09"','"RESEARCHOS_CHECK_ID":""','"RESEARCHOS_CASE_ID":"C19"','"RESEARCHOS_RETRIEVAL_MODE":"fixture"')))
check('bounded-owned-calls','],240)' in caller and '],420,T)' in caller and 'creation_flags=0x08000000' in caller)
check('all-guard-finally-closures',all('('+x+'_guard,"'+x+'")' in caller for x in ('compiler','candidate','runtime','input')))
check('locked-go-python-git',all(x in caller for x in ('cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b','d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490','da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f')))
check('no-retry-no-latest', 'latest' not in ''.join(line for line in caller.splitlines(True) if not line.lstrip().startswith('#')) and 'retry' not in caller)
check('owned-archive-before-status',caller.index('native-packet.public-index.json')<caller.index('assert result["actual_exit"]==0 and not result["timed_out"] and report'))
check('formal-unbound',C['formal_consumers']=='NOT_RUN_REGISTRY_UNBOUND' and 'formal_consumers="NOT_RUN_REGISTRY_UNBOUND"' in caller)

# Pure in-memory control: execute only the existing route validation function,
# supply synthetic raw-report bytes, and intercept its native verifier callee.
# This does not run the producer, Go, HTTP, SQLite, formal main, or accept a case.
router_raw=Path(C['sources']['ops/ci/w09_formal_router.py']['path']).read_bytes()
router_ast=ast.parse(router_raw)
closure_ast=ast.parse(Path(C['sources']['ops/ci/w09_evidence_closure.py']['path']).read_bytes())
names={'NATIVE','SOURCE_SCOPE','SELECTED'}
ns={'json':json,'ROOT':'SYNTHETIC_ROOT'}
for node in router_ast.body:
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in names:
  ns[node.targets[0].id]=ast.literal_eval(node.value)
native=next(x for x in router_ast.body if isinstance(x,ast.FunctionDef) and x.name=='_native_exact')
exec(compile(ast.Module(body=[native],type_ignores=[]),'<source-only-native-exact>','exec'),ns)
verify=next(x for x in closure_ast.body if isinstance(x,ast.FunctionDef) and x.name=='verify_native')
argv_nodes=[x for x in verify.body if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('packages','argv') for t in x.targets)]
check('callee-argv-exact-two-AST-statements',len(argv_nodes)==2)
selected=C['selected_tests'];ids=C['expected_native_ids'];run='0'*32
report=dict(status='PASS',task_id='W09',check_id=None,case_id='C19',scope='FIXTURE_IMPLEMENTED_SERVICE',exit_code=0,timed_out=False,assertion_ids=ids,expected_assertion_ids=ids,assertions=5,selected_tests=selected,passed_tests=sorted(selected),run_id=run,go_executable={'path':'SYNTHETIC_GO'},raw_evidence_references=['run-'+run+'/go-test.stdout.jsonl','run-'+run+'/go-test.stderr.txt'])
report['actual_invocation']=['SYNTHETIC_GO','test','-count=1','-json','-run','^(?:'+'|'.join(selected)+')$','./internal/domain']
report['assertion_results']=[dict(assertion_id=x,status='PASS',raw_evidence_reference=report['raw_evidence_references'][0]) for x in ids]
source=copy.deepcopy(report);source['report_reference']='run-'+run+'/report.json'
class MemoryReport:
 def read_bytes(self):return json.dumps(report).encode('utf-8')
ns['_pin']=lambda ref:{'path':ref,'synthetic_control':True}
ns['_inside_repo']=lambda ref:MemoryReport()
seen=[]
def intercept(root,src,rep,expected,actual_selected):
 local={'report':rep,'selected':actual_selected}
 exec(compile(ast.Module(body=argv_nodes,type_ignores=[]),'<exact-closure-argv-only>','exec'),local)
 assert local['argv']==src['actual_invocation']
 seen.append(dict(run_id=src['run_id'],selected_tests=actual_selected,actual_argv=local['argv'],report_reference=src['report_reference']))
 return {'SYNTHETIC_SOURCE_CONTROL_ONLY':True}
ns['verify_native']=intercept
for command in ('test.research.fixture','test.retrieval'):
 ns['_native_exact'](source,(command,'W09','','C19'))
 check('consumer-same-run-order:'+command,seen[-1]['selected_tests']==selected and seen[-1]['actual_argv']==report['actual_invocation'])
check('both-consumers-identical-run-and-argv',len(seen)==2 and seen[0]==seen[1])
for field,value in [('selected_tests',[selected[0],selected[0]]),('check_id','W09-G01'),('case_id','A06'),('assertion_ids',ids[:-1])]:
 bad=copy.deepcopy(source);bad[field]=value
 try:ns['_native_exact'](bad,('test.retrieval','W09','','C19'))
 except ValueError as error:check('negative-roster:'+field,str(error)=='NATIVE_ROSTER_OR_SCOPE_MISMATCH')
 else:raise AssertionError('invalid fixture accepted:'+field)

delta=[]
for i,(oldname,newname) in enumerate((('prepare_history20_five_parent.actual_owned.py','prepare_w09_c19.actual_owned.py'),('validate_history20_five_parent.actual_owned.py','run_w09_c19.actual_owned.py'))):
 oldpath=Path(C['base_driver_refs'][i]['path']);oldraw=oldpath.read_bytes();newraw=(N/newname).read_bytes()
 old=oldraw.decode('utf-8').splitlines(keepends=True);new=newraw.decode('utf-8').splitlines(keepends=True)
 ops=[]
 for tag,a,b,c,d in difflib.SequenceMatcher(a=old,b=new,autojunk=False).get_opcodes():ops.append(dict(op=tag,old_start=a,old_end=b,new_start=c,new_end=d,old_lines=old[a:b],new_lines=new[c:d]))
 check('complete-reverse-original-bytes:'+newname,''.join(line for op in ops for line in op['old_lines']).encode('utf-8')==oldraw)
 check('complete-forward-final-bytes:'+newname,''.join(line for op in ops for line in op['new_lines']).encode('utf-8')==newraw)
 delta.append(dict(original_ref=pin(oldpath),candidate_ref=pin(N/newname),opcodes=ops))
js('caller-exact-reversible-delta.final.json',delta)
check('all-original-inputs-unchanged-after-controls',all(Path(p).read_bytes()==raw for p,raw in initial.items()))
js('source-controls.result.final.json',dict(status='PASS_SOURCE_ONLY',checks=checks,check_count=len(checks),consumer_order_controls=seen,synthetic_control_only=True,native_executed=False,formal_consumer_main_executed=False,formal_acceptance=False))
print(json.dumps(dict(status='PASS_SOURCE_ONLY',check_count=len(checks),actual_native_executed=False)))
