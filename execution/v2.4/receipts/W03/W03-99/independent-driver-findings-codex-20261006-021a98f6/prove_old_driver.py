"""Synthetic integrity counterexamples only; no atom, Go or product execution."""
import copy,datetime,hashlib,json,math,os,pathlib,sys,types
from unittest.mock import patch
R=pathlib.Path('D:/作品集/ResearchOS/research-os');O=pathlib.Path(__file__).resolve().parent;B=O.parent;E=B/'executor_codex'
EXPECTED={'gate_driver.py':'0719ed7a808e7e59eb4f2d8a270fd5514b9e255a831341f49f6efbc3c58adf60','bridge.py':'a453849512368509487321d0ff1e503357d741e7660bf8d7886fd7b463b93cb0'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def raw(p,s):
 with p.open('x',encoding='utf-8') as f:f.write(s)
sources={}
for name,h in EXPECTED.items():
 assert sha(E/name)==h,(name,'old source changed')
 target=O/('snapshot_'+name)
 with target.open('xb') as f:f.write((E/name).read_bytes())
 sources[str(E/name)]=h
for source,name in [(E/'expected.json','snapshot_expected.json'),(R/'tests/contracts/fixtures/client_protocol_v2_fixtures.json','snapshot_fixture_corpus.json'),(R/'execution/commands.json','snapshot_legacy_commands.json'),(R/'execution/v2.4/commands.json','snapshot_current_commands.json')]:
 with (O/name).open('xb') as f:f.write(source.read_bytes())
 sources[str(source)]=sha(source)
g=types.ModuleType('frozen_old_gate');g.__file__=str(E/'gate_driver.py');exec(compile((O/'snapshot_gate_driver.py').read_bytes(),g.__file__,'exec'),g.__dict__)
bridge=types.ModuleType('frozen_old_bridge');bridge.__file__=str(E/'bridge.py');exec(compile((O/'snapshot_bridge.py').read_bytes(),bridge.__file__,'exec'),bridge.__dict__)
def prohibited(*args,**kwargs):raise AssertionError('Atom/product execution is forbidden in this proof')
g.run_gate=g.execute_atom=prohibited
p=read(O/'snapshot_expected.json');corpus=read(O/'snapshot_fixture_corpus.json')['fixtures'];facts={x['name']:x for x in corpus}
assert len(facts)==len(corpus)==106
projection={'CURRENT-SCHEMA-COMPILE','RUNTIME-SCHEMA-LOAD','CURRENT-LOCAL-REFS','RUNTIME-ENTITY-PROJECTION','RUNTIME-OPERATION-PROJECTION','RUNTIME-DEFINITION-PROJECTION','API-EMBEDDED-SCHEMA-EXACT','API-SCHEMA-LOAD','EVALUATION-OVERLAY-EXACT'}
checks=[]
for id in p['probe_ids']['W03-G01']:
 if id.startswith('FIXTURE/'):
  fx=facts[id.removeprefix('FIXTURE/')];group='fixtures';detail={k:fx[k] for k in ['expected_valid','schema_definition']};detail['actual_valid']=fx['expected_valid']
 elif id in {'CORPUS-SHAPE','PROTOCOL-INVENTORY'}:group='fixture_metadata';detail={'SYNTHETIC':True}
 else:group='projection' if id in projection else 'aggregate';detail={'SYNTHETIC':True}
 checks.append({'id':id,'group':group,'passed':True,'detail':detail})
probe={'SYNTHETIC_INTEGRITY_COUNTEREXAMPLE_NOT_PRODUCT_EVIDENCE':True,'status':'PASS','check_id':'W03-G01','formal_product_acceptance':'NOT_RUN','owned_acceptance_ids':[],'checks':checks}
assert len(checks)==124
cases=[]
def exercise(id,payload,call,old_expected,fixed_expected,explanation):
 filename=id+'.synthetic.txt';raw(O/filename,payload)
 try:parsed=call(payload);accepted=True;error=None
 except Exception as e:parsed=None;accepted=False;error=type(e).__name__+': '+str(e)
 assert accepted==old_expected,(id,accepted,error)
 result={'id':id,'synthetic_only':True,'old_parser_accepted':accepted,'expected_repaired_behavior':fixed_expected,'input_path':filename,'input_sha256':sha(O/filename),'actual_error':error,'parsed_result':parsed,'explanation':explanation}
 cases.append(result);return result
encode=lambda x:json.dumps(x,ensure_ascii=False,allow_nan=True)
probe_call=lambda value,exit=0:g.parse_probe(value,p['probe_ids']['W03-G01'],exit,'W03-G01')
exercise('control_complete106',encode(probe),probe_call,True,'ACCEPT_VALID_SYNTHETIC_CONTROL','124 synthetic checks with106 corpus-aligned fixture metadata rows; this does not execute or certify any product behavior.')
mutant=copy.deepcopy(probe);target=next(x for x in mutant['checks'] if x['group']=='fixtures' and x['detail']['expected_valid'] is True);target['detail']['actual_valid']=False
case=exercise('fixture_actual_contradicts_passed',encode(mutant),probe_call,True,'REJECT','One positive fixture reports actual_valid=false but passed=true; all IDs, groups and76/30 expected totals remain unchanged.');case['mutated_id']=target['id']
mutant=copy.deepcopy(probe);positive=next(x for x in mutant['checks'] if x['group']=='fixtures' and x['detail']['expected_valid'] is True);negative=next(x for x in mutant['checks'] if x['group']=='fixtures' and x['detail']['expected_valid'] is False and x['detail']['schema_definition']!=positive['detail']['schema_definition'])
old_pair={x['id']:copy.deepcopy(x['detail']) for x in [positive,negative]}
positive['detail'],negative['detail']=copy.deepcopy(negative['detail']),copy.deepcopy(positive['detail'])
case=exercise('fixture_expected_and_schema_swapped',encode(mutant),probe_call,True,'REJECT','A positive/negative pair swaps expected_valid, actual_valid and schema_definition; each row stays internally consistent and total76/30 remains, but both IDs contradict the pinned corpus.');case['original_pair']=old_pair;case['mutated_pair']={x['id']:x['detail'] for x in [positive,negative]}
events=[{'Action':'run','Test':'TestSynthetic','Package':'researchos.local/research-os/internal/domain'},{'Action':'pass','Test':'TestSynthetic','Package':'researchos.local/research-os/internal/domain'}]+[{'Action':'pass','Package':'researchos.local/research-os/'+x[2:]} for x in g.PACKAGES]
go_encode=lambda value:'\n'.join(encode(e) for e in value)
go_call=lambda value,exit=0:g.parse_go(value,['TestSynthetic'],exit)
exercise('control_go_test_identity',go_encode(events),go_call,True,'ACCEPT_VALID_SYNTHETIC_CONTROL','One expected synthetic test in domain plus the three registered package completions.')
mutant=copy.deepcopy(events)
for item in mutant[:2]:item['Package']='researchos.local/research-os/unregistered-package'
exercise('go_wrong_package_same_test_and_completions',go_encode(mutant),go_call,True,'REJECT','Run/pass retain the expected test name but claim an unregistered package; the three legitimate package completions remain.')
mutant=copy.deepcopy(events);mutant[1]['Elapsed']=float('nan')
exercise('nonfinite_NaN_go_event',go_encode(mutant),go_call,True,'REJECT','NaN is outside JSON but old loads accepts it and parse_go ignores the nonfinite elapsed field.')
mutant=copy.deepcopy(probe);mutant['elapsed']=float('inf')
exercise('nonfinite_Infinity_probe',encode(mutant),probe_call,True,'REJECT','Infinity is outside JSON but old loads/parse_probe accept it as unrelated payload metadata.')
exercise('boolean_false_go_exit',go_encode(events),lambda value:go_call(value,False),True,'REJECT','Python False==0 makes a non-integer exit code pass the old Go parser.')
exercise('boolean_false_probe_exit',encode(probe),lambda value:probe_call(value,False),True,'REJECT','Python False==0 makes a non-integer exit code pass the old probe parser.')
exercise('control_nonzero_exit_refused',go_encode(events),lambda value:go_call(value,7),False,'REJECT','Valid-looking Go output with real nonzero integer exit is already refused.')
mutant=copy.deepcopy(probe);mutant['checks'][0]['passed']=False
exercise('control_failed_check_refused',encode(mutant),probe_call,False,'REJECT','An explicit failed check is already refused; the finding concerns contradictory details hidden behind passed=true.')
# Compare actual legacy registry argv/env against the old bridge transport.
# All environment contents below are synthetic or public fixed configuration.
# Replace subprocess.call with an in-process recorder; no child is launched.
legacy=read(O/'snapshot_legacy_commands.json')['commands']['contracts.validate'];current=read(O/'snapshot_current_commands.json')['commands']['contracts.validate']
tools={'RESEARCHOS_GO':'SYNTHETIC_LOCKED_GO','RESEARCHOS_NODE':'SYNTHETIC_LOCKED_NODE','RESEARCHOS_NPM_CLI':'SYNTHETIC_LOCKED_NPM'}
selectors={'RESEARCHOS_TASK_ID':'W06','RESEARCHOS_CHECK_ID':'W06-G01','RESEARCHOS_CASE_ID':'A03'}
base={'SystemRoot':'SYNTHETIC_SYSTEM_ROOT','PATH':'SYNTHETIC_PATH','TEMP':'SYNTHETIC_TEMP','TMP':'SYNTHETIC_TMP'}
launch={**base,**current['fixed_env'],**tools,**selectors}
expected_env={**base,**legacy['fixed_env'],**tools,**selectors}
expected_argv=[sys.executable,*legacy['argv']]
captured={}
def intercept(argv,**kwargs):
 captured.update(argv=argv,cwd=str(kwargs['cwd']),environment=dict(kwargs.get('env',os.environ)),stream_arguments={k:v for k,v in kwargs.items() if k in {'stdout','stderr','capture_output'}},child_was_executed=False)
 return 37
bridge.subprocess=types.SimpleNamespace(call=intercept)
with patch.object(sys,'argv',['bridge.py','contracts.validate']),patch.dict(os.environ,launch,clear=True):
 result=bridge.main()
assert result==37 and captured['stream_arguments']=={} and captured['child_was_executed'] is False
transport={'synthetic_only':True,'registry_key':'contracts.validate','selectors':selectors,'legacy_registry_sha256':sources[str(R/'execution/commands.json')],'current_registry_sha256':sources[str(R/'execution/v2.4/commands.json')],'expected_legacy_argv':expected_argv,'expected_legacy_environment':expected_env,'actual_intercepted_call':captured,'actual_return_code':result,'subprocesses_executed':0}
save(O/'legacy_transport.synthetic.json',transport)
assert captured['argv']!=expected_argv and captured['environment']!=expected_env
cases.append({'id':'legacy_original_argv_not_preserved','synthetic_only':True,'actual_match':False,'expected_repaired_behavior':'MATCH_LEGACY_REGISTRY_ARGV','input_path':'legacy_transport.synthetic.json','input_sha256':sha(O/'legacy_transport.synthetic.json'),'explanation':'Old registry specifies python -X utf8 ops/ci/contracts.py; old bridge strips the interpreter arguments.'})
cases.append({'id':'legacy_fixed_env_not_restored','synthetic_only':True,'actual_match':False,'expected_repaired_behavior':'MATCH_LEGACY_BRANCH_ENVIRONMENT','input_path':'legacy_transport.synthetic.json','input_sha256':sha(O/'legacy_transport.synthetic.json'),'explanation':'Legacy branch inherits the new child environment, omits legacy RESEARCHOS_EXECUTOR_ID=codex:/root and retains branch-specific GOPATH/GOCACHE. Original streams and simulated exit37 are preserved.'})
assert all(sha(pathlib.Path(path))==h for path,h in sources.items()),'reviewed main inputs changed during proof'
save(O/'counterexample_results.json',cases)
manifest={'scope':'SYNTHETIC_DRIVER_INTEGRITY_ONLY_NOT_PRODUCT_OR_LIVE_OR_FRESH_ATOM_EVIDENCE','source_hashes':sources,'case_count':len(cases),'product_or_atom_subprocesses':0,'files':[{'path':x.name,'sha256':sha(x)} for x in sorted(O.iterdir()) if x.is_file()]}
save(O/'manifest.json',manifest)
review={'schema':'researchos.independent-driver-integrity-findings.v1','step_id':'W03-99','reviewer':'codex:/root/w1702_review','actual_model':'gpt-6-astra','reasoning_effort':'high','independent_of_executor':True,'verdict':'CONFIRMED_OLD_DRIVER_INTEGRITY_GAPS_PENDING_REPAIR','old_source_hashes':EXPECTED,'pure_memory':True,'case_count':len(cases),'accepted_invalid_parser_counterexamples':7,'legacy_transport_mismatches':2,'positive_controls':2,'negative_controls':2,'findings':[{'id':'W0399-FIXTURE-DETAIL-CORPUS-BINDING','status':'CONFIRMED_OPEN','counterexamples':['fixture_actual_contradicts_passed','fixture_expected_and_schema_swapped'],'required_boundary':'Require strict bool actual/expected equality and per-ID expected_valid/schema_definition equality with the pinned106 corpus.'},{'id':'W0399-GO-PACKAGE-TEST-IDENTITY','status':'CONFIRMED_OPEN','counterexamples':['go_wrong_package_same_test_and_completions'],'required_boundary':'Bind expected(package,test) identity, not only test-name counts and unrelated package-completion totals.'},{'id':'W0399-LEGACY-TRANSPORT-CONTRACT','status':'CONFIRMED_OPEN','counterexamples':['legacy_original_argv_not_preserved','legacy_fixed_env_not_restored'],'required_boundary':'Match actual old registry argv and branch-specific fixed environment while preserving child Go environment, inherited streams and exact exit semantics.'},{'id':'W0399-STRICT-JSON-EXIT-TYPES','status':'CONFIRMED_OPEN','counterexamples':['nonfinite_NaN_go_event','nonfinite_Infinity_probe','boolean_false_go_exit','boolean_false_probe_exit'],'required_boundary':'Reject nonfinite JSON; require integer non-bool exit_code before testing zero.'}],'evidence_manifest':{'path':str(O/'manifest.json'),'sha256':sha(O/'manifest.json')},'results':{'path':str(O/'counterexample_results.json'),'sha256':sha(O/'counterexample_results.json')},'limitations':['These synthetic payloads are deliberately not product observations and are not atom receipts. No raw product evidence was forged, indexed or replaced.','Only frozen old source parsers and intercepted legacy transport ran. No new driver repair is accepted by this record.','Current gate singleton/mode/source/tool checks outside these parser/transport examples were reviewed statically and are not invalidated by implication.','Existing explicit failed-check and nonzero-exit negatives remain rejected. No run_gate or execute_atom call occurred.'],'parent_card_accepted':False,'formal_cases_accepted':[],'formal_case_count_delta':0,'product_Go_GUI_provider_service_private_label_operations':0,'source_shared_metadata_edits':0,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(B/'independent_driver_findings_codex.json',review)
print(json.dumps({'verdict':review['verdict'],'cases':len(cases),'invalid_parser_accepted':7,'transport_mismatches':2,'product_processes':0,'findings_sha256':sha(B/'independent_driver_findings_codex.json'),'manifest_sha256':sha(O/'manifest.json')}))
