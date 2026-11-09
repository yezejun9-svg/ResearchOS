import sys
sys.dont_write_bytecode=True
import ast,copy,difflib,hashlib,importlib.util,json,os,re,traceback
from pathlib import Path
O=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
U=B/'integration_codex/python-broker4-public-units-root-1791512710000';V=U/'revision-explicit-binary-handles'
C=B/'integration_codex/native-broker4-controller-config-root-1791513411000'
SP=B/'integration_codex/native-broker4-positive-serve-root-1791513411000/serve_one_positive_broker4.actual_owned.py'
AP=B/'integration_codex/native-broker4-positive-root-api-1791513411000/root_public_api_broker4.actual.py'
A=B/'integration_codex/native-temp-compile-unit-root-1791508539969/revision-list-manifest'
OLD=B/'integration_codex/native-temp-controller-config-root-1791508950616'
PRIOR=B/'native_temp_prelaunch_actual_independent_review_codex/b5bf0ed767204b69a82b86acff0e23f1'
checks=[];guard=None
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def norm(r):return {'path':str(Path(r['path'])),'sha256':r['sha256'].removeprefix('sha256:'),'bytes':r['bytes']}
def key(p):return str(Path(p)).casefold()
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def check(n,v,detail=None):checks.append({'check':n,'passed':bool(v),'detail':detail})
def load(p):return json.loads(Path(p).read_bytes())
def goodguard(g):return g['verification']=='PASSED' and g['closed'] is True and g['retained_handles_count']==0 and g['failure'] is None and g['errors']==[] and all(x['verified'] and x['final_path_match'] and x['closed'] for x in g['entries'])
def main():
 global guard
 cfg=load(C/'controller.public.config.json');hc=load(C/'native-harness.public.config.json');prep=load(C/'controller-config.prepared.json')
 inv=load(V/'units.invocation.json');unitclosed=load(V/'validation.closed.json');res=load(V/'units.results.json')
 invresources=load(V/'python-public-unit-runtime-inventory.json')['resources']
 actual=load(A/'validation.closed.json');formatted=load(A/'formatted.source-members.json')
 caller=load(C/'caller-adaptation.provenance.json');builder=load(C/'configuration-builder.adaptation.provenance.json')
 refs=list(cfg['FrozenInputs'])+invresources+formatted
 for d in [U,V,C,SP.parent,AP.parent]:
  refs.extend(pin(p) for p in d.iterdir() if p.is_file())
 refs.extend(pin(OLD/n) for n in ['controller.public.config.json','native-harness.public.config.json'])
 refs.extend([pin(Path(__file__)),pin(PRIOR/'HDF.json'),pin(PRIOR/'MF.json'),pin(A/'formatted.source-members.json')])
 refs.extend(x[k] for x in caller['sources'] for k in ['base_source_ref','new_source_ref'])
 refs.extend(builder[k] for k in ['base_source_ref','new_source_ref'])
 for p in [V/'input-source-guard.cleanup.actual.json',V/'runtime-source-guard.cleanup.actual.json',C/'bootstrap-source-guard.cleanup.actual.json']:
  refs.extend(load(p)['entries'])
 unique={}
 for r in refs:
  q=norm(r);k=key(q['path'])
  if k in unique:assert unique[k]==q,('conflicting pins',q['path'])
  unique[k]=q
 refs=list(unique.values())
 before=[pin(r['path']) for r in prep['canonical_unchanged_refs']]
 gp=norm(cfg['SourceReadGuard'])
 assert pin(gp['path'])==gp and gp['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
 spec=importlib.util.spec_from_file_location('independent_c10_guard',gp['path']);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
 guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);guard.acquire(refs)
 def raw(p):return guard.get_buffer(str(Path(p)))
 def read(p):return json.loads(raw(p))
 def verified(r):return hashlib.sha256(raw(r['path'])).hexdigest()==r['sha256'].removeprefix('sha256:') and len(raw(r['path']))==r['bytes']
 def mapping(rs):return {key(r['path']):norm(r) for r in rs}
 frozen=mapping(cfg['FrozenInputs'])
 def frozenhas(r):return frozen.get(key(r['path']))==norm(r)
 save('input-pins.json',refs)
 anchors=[(V/'validation.closed.json','9f9d17cfdcea867bf03bd1404ec1bd8b1824229add2a2b03d107c0ce2cb6c318',1149),(C/'controller.public.config.json','48c06dc2c88326a98cd785b364d6daf5fad363292a7a4f97fd209938d54273b2',1178613),(C/'controller-config.prepared.json','50a6e86439e4faaf46916c117b8b7ae05484321286a52dd1004a038e5d28289b',5033),(SP,'31295d5c366b9671e3e3b293ee80111d9b4ac2db22c667ca83c8567907148f06',5857),(AP,'6eeae42516cdb6cad02f09555747c103e4e736c0ca4752dfe210a66c975fb04b',14698)]
 for p,h,n in anchors:check('fixed-anchor:'+p.name,hashlib.sha256(raw(p)).hexdigest()==h and len(raw(p))==n)
 for k in ['results_ref']:check('unit-closed-binding:'+k,verified(unitclosed[k]))
 for k in ['invocation_ref','stdout_ref','stderr_ref']:check('unit-result-binding:'+k,verified(res[k]))
 for k in ['broker_source_ref','unit_source_ref','runtime_inventory_ref']:check('unit-invocation-binding:'+k,verified(inv[k]))
 source=raw(inv['unit_source_ref']['path']).decode();tree=ast.parse(source)
 cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='PublicEnvironmentBoundaryTests')
 methods=sorted(x.name for x in cls.body if isinstance(x,ast.FunctionDef) and x.name.startswith('test_'))
 stderr=raw(V/'units.stderr.raw').decode();stdout=raw(V/'units.stdout.raw').decode()
 terms=re.findall(r'^(test_\S+) \(__main__\.PublicEnvironmentBoundaryTests\.(test_\S+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\r\n]*)$',stderr,re.M)
 check('actual17-exact-testnames-and-ok',len(terms)==17 and sorted(x[0] for x in terms)==methods==res['test_method_names'] and all(a==b and c=='ok' for a,b,c in terms))
 check('actual-unittest-terminal-17-OK',re.search(r'Ran 17 tests in [0-9.]+s\r?\n\r?\nOK\r?\n?$',stderr) is not None and stdout.strip()=='ROOT_PYTHON_EXIT=0')
 check('actual17-result-counts',res['pass_count']==17 and res['fail_count']==res['skip_count']==0 and res['actual_python_child_exit']==0 and res['owned_job_closed'])
 owned=inv['owned_process'];j=owned['job_cleanup']
 check('actual-python-child-exact-identity',owned['owned_child_pid']==49484 and type(owned['creation_time_100ns']) is int and owned['creation_time_100ns']==134359857128271247 and owned['actual_exit']==0 and owned['timed_out'] is False and owned['error'] is None and owned['resumed'])
 check('actual-owned-job-closed',all(j[k] is True for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']) and j['active_processes_last_observed']==0 and j['errors']==[] and unitclosed['job_cleanup']==j)
 save('actual-unit-owned-job.json',{'pid':owned['owned_child_pid'],'creation_time_100ns_decimal':str(owned['creation_time_100ns']),'actual_exit':0,'job_cleanup':j,'FILETIME_policy':'Python int parsed, decimal string emitted; never JavaScript Number'})
 check('unit-fixed-argv',inv['argv'][1:6]==['-I','-S','-B','-X','utf8'] and Path(inv['argv'][6])==Path(inv['unit_source_ref']['path']) and inv['argv'][7]=='--broker-source' and Path(inv['argv'][8])==Path(inv['broker_source_ref']['path']) and inv['argv'][9:]==['--broker-sha256','70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c','--verbosity','2'])
 uio=read(U/'original-root-tool-io.json');ur=uio['revision_actual']['result']
 check('original-parent-unit-actual0',ur['chunk_id']=='c32831' and ur['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in ur['output'])
 ug=read(V/'input-source-guard.cleanup.actual.json');rg=read(V/'runtime-source-guard.cleanup.actual.json')
 check('unit-input-and-runtime-guards-closed',goodguard(ug) and goodguard(rg))
 check('unit-runtime321-exact-held-closure',len(invresources)==unitclosed['runtime_ref_count']==321 and mapping(invresources)==mapping(rg['entries']))
 initial_refs=[inv['broker_source_ref'],inv['unit_source_ref'],pin(V/'validate_python_broker4_public_units_revision.actual_owned.py'),pin(inv['argv'][0]),cfg['SourceReadGuard'],cfg['OriginalOwnedHelper']]
 for package in [Path(inv['broker_source_ref']['path']).parent,B/'native_python_broker_temp_env_independent_review_codex/9e4f389d093d4ea58eb5ec06e102876d']:
  pm=read(package/'MF.json');members=pm['members'].values() if isinstance(pm['members'],dict) else pm['members']
  initial_refs += [pin(package/'HDF.json'),pin(package/'MF.json')]+list(members)
 check('unit-source48-deduplicates44-exact-guard',len(initial_refs)==unitclosed['source_input_ref_count']==48 and len(mapping(initial_refs))==44 and mapping(initial_refs)==mapping(ug['entries']))
 check('unit-qualification-scopes-kept',res['alias_scope']=='MOCK_ONLY_NO_ACTUAL_JUNCTION' and res['canonical_path_scope']=='PATH_NORMALIZED_PHYSICAL_CANONICAL' and res['system_descendant_dedicated_test'] is False and res['no_broker_main_or_private_helper_call'])
 failed=read(U/'units.invocation.json')['owned_process'];qual=read(U/'failure879.exit-qualification.json')
 check('879-no-child-preparation-failure-preserved',failed['stage']=='PREPARE_EXPLICIT_STD_HANDLES' and failed['actual_exit'] is None and failed['owned_child_pid'] is None and failed['creation_time_100ns'] is None and failed['resumed'] is False and failed['job_cleanup']['handles_closed'] and qual['actual_outer_exit']==qual['actual_python_driver_exit']==1 and qual['actual_unit_child_exit'] is None and qual['actual_native_exit'] is None and qual['unit_tests_executed']==0 and verified(qual['immutable_origin_ref']) and verified(qual['invocation_ref']))
 check('879-no-uncreated-raw-read',not (U/'units.stdout.raw').exists() and not (U/'units.stderr.raw').exists())
 e881=read(U/'failure-origin.881.json')
 check('881-read-error-kept-distinct',e881['ordinal']==881 and e881['actual_outer_exit']==0 and e881['actual_python_exit'] is None and e881['actual_native_exit'] is None and 'because it does not exist' in e881['result']['output'])
 olddriver=raw(U/'validate_python_broker4_public_units.actual_owned.py')
 replacement=b'with (O/"units.stdout.raw").open("xb") as out, (O/"units.stderr.raw").open("xb") as err:\n  result=helper.run_owned(argv,str(R),env,out,err,60,creation_flags=0x08000000)'
 oldcall=b'result=helper.run_owned(argv,str(R),env,str(O/"units.stdout.raw"),str(O/"units.stderr.raw"),60,creation_flags=0x08000000)'
 reconstructed=olddriver.replace(oldcall,replacement).replace(b'python-broker4-public-units-env-1791512710000',b'python-broker4-public-units-env-1791512710000-revision1')
 check('unit-driver-revision-only-binary-handles-and-fresh-scratch',olddriver.count(oldcall)==1 and reconstructed==raw(V/'validate_python_broker4_public_units_revision.actual_owned.py'))
 check('unit-scratch-cleaned',not Path(inv['public_environment']['TEMP']).exists())
 check('C10-schema12keys',len(cfg)==12 and cfg['Schema']=='researchos.root-native-migration-controller.v1')
 check('C10-frozen4347-unique',len(cfg['FrozenInputs'])==len(frozen)==prep['frozen_input_count']==4347)
 fg=read(C/'config-input-source-guard.cleanup.actual.json');bg=read(C/'bootstrap-source-guard.cleanup.actual.json')
 check('C10-root-full-and-bootstrap-guards-closed',goodguard(fg) and goodguard(bg))
 expected_full={**frozen,key(C/'controller.public.config.json'):pin(C/'controller.public.config.json')}
 check('C10-full4348-exact-guard',len(fg['entries'])==4348 and mapping(fg['entries'])==expected_full)
 check('C10-bootstrap419-subset-frozen',len(bg['entries'])==419 and all(frozenhas(r) for r in bg['entries']))
 for k,v in cfg.items():
  if isinstance(v,dict) and {'path','sha256','bytes'} <= set(v):check('C10-reference:'+k,verified(v) and frozenhas(v))
 check('C10-harness-config-exact-full-pin',norm(prep['harness_config_ref'])==pin(C/'native-harness.public.config.json') and hc['CaseID']=='t10b4c239054ab67' and hc['Case']=='positive-replay' and Path(hc['OutputDirectory'])==C/'harness-facts')
 expected_roles={'RootProgram':'root-program','ControlProgram':'control-program','BackupProgram':'backup-program','EnrollmentProgram':'enrollment-build','PythonProgram':'python-program','BrokerSource':'broker-source','PrivateStdinHelper':'private-stdin-helper'}
 for k in expected_roles:check('HC-RawPin:'+k,set(hc[k])=={'role','path','sha256','bytes'} and hc[k]['role']==expected_roles[k] and verified(hc[k]) and frozenhas(hc[k]))
 check('HC-new-broker-exact',norm(hc['BrokerSource'])==norm(inv['broker_source_ref']) and hc['BrokerSource']['sha256']=='sha256:70b8eba1de168849d041488ac9268da60fd2ae8a059cc9518e9dc93d0cd4b87c' and hc['BrokerSource']['bytes']==8562)
 oldhc=read(OLD/'native-harness.public.config.json')
 check('HC-only-case-output-broker-changed',{k:v for k,v in hc.items() if k not in ['CaseID','OutputDirectory','BrokerSource']}=={k:v for k,v in oldhc.items() if k not in ['CaseID','OutputDirectory','BrokerSource']})
 oldcfg=read(OLD/'controller.public.config.json')
 check('C10-test-controller-helpers-build-inventory-unchanged',all(cfg[k]==oldcfg[k] for k in ['ControllerSource','TestProgram','ObservedOwnedHelper','OriginalOwnedHelper','SourceReadGuard','CompilerInventory','BuildInvocation']))
 labels={'RootProgram':'maintenance-root-build','ControlProgram':'control-build','BackupProgram':'backup-build','EnrollmentProgram':'enrollment-build'}
 check('N8-four-programs-tagtest-reused-exact',all(norm(hc[k])==norm(actual['binary_refs'][v]) for k,v in labels.items()) and norm(cfg['TestProgram'])==norm(actual['binary_refs']['tagged-test-harness']))
 check('N8-original-compile-accepted-anchor',verified(prep['compile_ref']) and prep['compile_ref']['sha256']=='sha256:9ecbf95ad3c89757479f611742a081d31aff0bbffbd1277aa1d10e0e82d52f5d' and read(PRIOR/'HDF.json')['decision']=='COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL')
 check('N8-43-current-sources-unchanged-frozen',len(formatted)==actual['source_count']==43 and all(verified(r) and frozenhas(r) for r in formatted))
 inventory=read(cfg['CompilerInventory']['path'])
 check('compiler-product-tool-whole-inventory-frozen',len(inventory['build_inputs'])==3793 and len(inventory['product_inventory'])==599 and len(inventory['compiler_tool_refs'])==8 and all(frozenhas(r) for r in inventory['build_inputs']+inventory['product_inventory']+inventory['compiler_tool_refs']))
 check('Go-and-official-test2json-explicitly-frozen',frozenhas(inventory['GoRef']) and frozenhas(prep['official_test2json_ref']) and prep['official_test2json_ref']==actual['official_test2json_ref'])
 go=Path(inventory['GoRef']['path'])
 check('Go-VERSION-and-module-frozen',all(key(p) in frozen for p in [go.parent.parent/'VERSION',go.parent.parent/'src/go.mod']))
 for rr in prep['source_review_refs']:check('source-review-reference-frozen:'+Path(rr['path']).parent.name+'/'+Path(rr['path']).name,verified(rr) and frozenhas(rr))
 proof_coverage={p.name:frozenhas(pin(p)) for p in V.iterdir() if p.is_file()}
 save('unit-proof-freeze-scope.json',{'direct_frozen':proof_coverage,'all_unit_directory_files_freshly_guarded_by_reviewer':True,'reference_bound_raws_runtime_driver_not_all_direct_FrozenInputs':True,'global_provider_requests':None})
 check('unit-proof-anchors-direct-frozen',all(proof_coverage[n] for n in ['validation.closed.json','units.results.json','units.invocation.json','input-source-guard.cleanup.actual.json','runtime-source-guard.cleanup.actual.json']))
 e=cfg['Environment'];temp=Path(e['TEMP']);local=R/'.local';trial=local/'mu-sdk-isolated-project-ed84838046934329a76733a005c9b162'
 def contains(parent,child):
  try:return os.path.commonpath([str(parent).casefold(),str(child).casefold()])==str(parent).casefold()
  except ValueError:return False
 check('fresh-isolated-proof-TEMP-TMP-exact',e['TEMP']==e['TMP']==e['RESEARCHOS_NATIVE_MIGRATION_HARNESS_TEMP_ROOT']==prep['public_temp_binding'] and temp.is_absolute() and temp.is_dir() and str(temp.resolve()).casefold()==str(temp).casefold() and contains(local,temp) and temp!=local and not contains(trial,temp) and not contains(temp,trial) and all(not contains(Path(e[k]),temp) and not contains(temp,Path(e[k])) for k in ['SystemRoot','WINDIR']))
 check('fresh-runtime-and-facts-absent',not Path(cfg['ControllerDirectory']).exists() and not Path(hc['OutputDirectory']).exists())
 check('pure-context-prepared-no-native-authority',prep['no_automatic_sign_or_approval'] is True and all(prep[k]==0 for k in ['native_cases_executed','Owner_credential_reads','private_key_reads','issuer_signatures','original_trial_DB_writes','provider_requests']) and prep['formal_acceptance'] is False)
 cio=read(C/'original-root-tool-io.json')
 check('context-original-tool-completion0',cio['preparation']['result']['chunk_id']=='2db48c' and cio['preparation']['result']['session_id']==31211 and cio['completion']['chunk_id']=='90ba53' and cio['completion']['exit_code']==0 and 'ROOT_PYTHON_EXIT=0' in cio['completion']['output'])
 for item in caller['sources']:
  base=raw(item['base_source_ref']['path']);candidate=raw(item['new_source_ref']['path']);inverse=candidate
  for r in reversed(item['exact_replacements']):inverse=inverse.replace(r['new'].encode(),r['old'].encode())
  check('caller-exact-inverse:'+Path(item['new_source_ref']['path']).name,verified(item['base_source_ref']) and verified(item['new_source_ref']) and inverse==base and len(item['exact_replacements'])==3)
  bdefs={x.name:ast.dump(x) for x in ast.parse(base).body if isinstance(x,ast.FunctionDef)};cdefs={x.name:ast.dump(x) for x in ast.parse(candidate).body if isinstance(x,ast.FunctionDef)}
  check('caller-all-function-AST-unchanged:'+Path(item['new_source_ref']['path']).name,bdefs==cdefs)
 # Interpret only literal byte replacement declarations from the source adaptation script.
 rawbase=raw(builder['base_source_ref']['path']);generated=rawbase;bindings={};edits=[]
 gen=ast.parse(raw(C/'prepare_broker4_context_builder_source.actual.py'))
 def literal(node):
  if isinstance(node,ast.Constant) and isinstance(node.value,bytes):return node.value
  if isinstance(node,ast.Name):return bindings[node.id]
  if isinstance(node,ast.BinOp) and isinstance(node.op,ast.Add):return literal(node.left)+literal(node.right)
  raise ValueError('non-literal source adaptation')
 for stmt in gen.body:
  if not isinstance(stmt,ast.Assign) or len(stmt.targets)!=1 or not isinstance(stmt.targets[0],ast.Name):continue
  name=stmt.targets[0].id
  if name in ['extra','before','insert']:bindings[name]=literal(stmt.value)
  elif name=='raw' and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Attribute) and isinstance(stmt.value.func.value,ast.Name) and stmt.value.func.value.id=='raw' and stmt.value.func.attr=='replace':
   a,b=map(literal,stmt.value.args);count=generated.count(a);generated=generated.replace(a,b);edits.append({'old':a.decode(),'new':b.decode(),'replacement_count':count})
 check('builder-exact-declared-literal-transform',verified(builder['base_source_ref']) and verified(builder['new_source_ref']) and generated==raw(builder['new_source_ref']['path']) and all(x['replacement_count']==1 for x in edits))
 save('builder-literal-adaptations.json',edits)
 with (O/'builder-exact.diff').open('xb') as f:f.write(''.join(difflib.unified_diff(rawbase.decode().splitlines(True),generated.decode().splitlines(True),fromfile='accepted-T8-builder',tofile='C10-builder')).encode())
 check('builder-function-AST-unchanged',{x.name:ast.dump(x) for x in ast.parse(rawbase).body if isinstance(x,ast.FunctionDef)}=={x.name:ast.dump(x) for x in ast.parse(generated).body if isinstance(x,ast.FunctionDef)})
 check('caller-private-sign-release-TTL-preserved',caller['private_input_signing_release_and_TTL_behaviors_unchanged'] is True and caller['auto_sign'] is False and caller['native_started'] is False and builder['TTL_and_signing_rules_unchanged'] is True)
 check('CP362-current-fixed',before[0]['sha256']=='84c970d86ab96b78a7621595839005f68a440fc9a540d3b619500c7cbed2669b' and before[0]['bytes']==4195882 and before==[norm(r) for r in prep['canonical_unchanged_refs']])
 after=[pin(r['path']) for r in prep['canonical_unchanged_refs']]
 check('canonical-before-after-identical',before==after)
 save('canonical-pins.json',{'before':before,'after':after,'Root_sole_canonical_writer':True})
 cleanup=guard.close();save('guard-closure.json',cleanup);check('reviewer-all-guards-closed',goodguard(cleanup))
 report={'schema':'researchos.independent-broker4-public17-prelaunch-review.v1','decision':'COMPONENT_ACCEPTED_PRELAUNCH_CONDITIONAL' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES','authority':'NONE','formal_acceptance':False,'checks':checks,'guarded_public_inputs':len(refs),'actual_public_boundaries':{'PASS':17,'FAIL':0,'SKIP':0},'native_positive_Owner_nine_business_formal_accepted':False,'reviewer_native_Go_SQL_key_sign_context_provider_execution':False,'original_trial_provider_requests':None,'global_provider_requests':None,'new_mechanical_errors':0,'history_reset':False,'stop':True}
 save('review.json',report)
 print(json.dumps({'decision':report['decision'],'passed':sum(x['passed'] for x in checks),'total':len(checks),'failed':[x for x in checks if not x['passed']],'guarded_public_inputs':len(refs),'all_guards_closed':cleanup['closed']},ensure_ascii=False))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if guard is not None:
  cleanup=guard.close()
  if not (O/'guard-closure.json').exists():save('guard-closure.json',cleanup)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)

