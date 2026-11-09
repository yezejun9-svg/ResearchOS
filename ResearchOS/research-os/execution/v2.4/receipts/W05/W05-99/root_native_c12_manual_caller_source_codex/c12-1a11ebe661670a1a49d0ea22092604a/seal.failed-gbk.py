from pathlib import Path
import ast,json,hashlib
N=Path(__file__).parent
def pin(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def put(name,v):(N/name).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
refs=json.loads((N/'input-pins.json').read_text())
for ref in refs:assert pin(Path(ref['path']))==ref
config=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/native-cleanup-controller-source-root-1791517434000/controller.public.config.json')
config_ref=pin(config)
assert config_ref['sha256']=='38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256' and config_ref['bytes']==1106152
refs.append(config_ref)
changes=json.loads((N/'source-replacements.json').read_text())
control=[]
for change in changes:
 candidate=Path(change['candidate']);base=Path(change['base']['path']);raw=candidate.read_bytes();txt=raw.decode().replace('\r\n','\n')
 for old,new in reversed(change['replacements']):
  assert txt.count(new)==1;txt=txt.replace(new,old)
 original=base.read_bytes();newline='\r\n' if b'\r\n' in original else '\n'
 assert txt.replace('\n',newline).encode()==original
 ca=ast.parse(raw);ba=ast.parse(original)
 cf={n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ca) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
 bf={n.name:ast.dump(n,include_attributes=False) for n in ast.walk(ba) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
 assert cf==bf
 control.append({'candidate':pin(candidate),'original':pin(base),'exact_byte_inverse':True,'all_original_functions_classes_AST_identical':True,'original_definitions':len(bf)})
serve=(N/'serve_one_positive_c12.actual_owned.py').read_text();api=(N/'root_public_api_c12.actual.py').read_text()
assert 'env,stdout,stderr,1800,creation_flags' in serve
assert '"--child","--config-sha256",expected_config_sha,"--config-bytes",str(expected_config_bytes)' in serve
assert '1440' not in serve and '1440' not in api
assert 'config_plain["sha256"]==expected_config_sha and config_plain["bytes"]==expected_config_bytes' in serve
assert 'config_plain["sha256"]==expected_config_sha and config_plain["bytes"]==expected_config_bytes' in api
prep=(N/'prepare_one_root_request.py').read_text();tree=ast.parse(prep)
imports=[]
for n in ast.walk(tree):
 if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
 elif isinstance(n,ast.ImportFrom):imports.append(n.module)
assert set(imports)=={'sys','hashlib','json','re','datetime','pathlib'}
calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
for call in calls:
 name=call.func.id if isinstance(call.func,ast.Name) else call.func.attr if isinstance(call.func,ast.Attribute) else ''
 assert name not in {'exec','eval','compile','Popen','run','system','connect','sleep','poll','sign_reviewed','publish_signed','release_fixture','prepare','serve','mkdir'},name
assert not any(isinstance(n,(ast.While,ast.AsyncFor)) for n in ast.walk(tree))
assert 'style="bare"' in prep and 'request["InspectionReceipt"] = normalized' in prep
assert 'inspection["database_ref"]' not in prep
assert '(expires - issued).total_seconds() == 240' in prep
assert 'with destination.open("xb")' in prep and 'no future or unrelated request fields' in prep
assert 'API_SHA = "'+pin(N/'root_public_api_c12.actual.py')['sha256']+'"' in prep
assert 'bytes='+str(pin(N/'root_public_api_c12.actual.py')['bytes']) in prep
assert 'NH1_SHA = "122f586885a2f3cd8141f4697175655d03441667603fc378cdac662e21a65ac2"' in prep
for p in N.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
checks={'scope':'PURE_SOURCE_STATIC_ONLY','caller_controls':control,'python_AST_parsing':True,'preparer_no_native_SQL_API_helper_invocation_or_poll_loop':True,'explicit_config_argv_pin_and_child_forwarding':True,'separate_fixed_existing_output_directories':True,'one_action_phase_exact_spec':True,'actual_existing_refs_required':True,'nested_database_ref_not_normalized_or_opened':True,'four_minute_grant_preserved':True,'outer_timeout_authorized_correction':{'old_actual':1440,'new':1800,'old_source_unchanged':True},'config_created_or_modified':False,'Root_supplied_actual_config_hash_checked':config_ref,'native_Go_SQL_Git_model_executed':False,'NH1_or_API_or_controller_executed':False,'approvals_generated':False,'runtime_validation':'PENDING_ROOT','new_failure_origins':[]}
put('static-controls.json',checks)
put('sourceguard.final.json',{'inputs':refs,'all_unchanged':True,'canonical_guards_held':False,'canonical_written':False})
members=[pin(p) for p in sorted(N.rglob('*')) if p.is_file() and p.name not in {'HDF.json','MF.json','seal.original-tool-io.json'}]
put('MF.json',{'schema':'researchos.source-manifest.v1','scope':'SOURCE_ONLY','members':members})
h={'schema':'researchos.c12-root-manual-caller-source-handoff.v1','status':'SOURCE_PREPARED_PENDING_NONAUTHOR_REVIEW_AND_ROOT_EXECUTION','case_id':'t12cl149d6f49321','manifest_ref':pin(N/'MF.json'),'manifest_member_count':len(members),'serve_ref':pin(N/'serve_one_positive_c12.actual_owned.py'),'api_ref':pin(N/'root_public_api_c12.actual.py'),'preparer_ref':pin(N/'prepare_one_root_request.py'),'instructions_ref':pin(N/'README.md'),'static_ref':pin(N/'static-controls.json'),'guard_ref':pin(N/'sourceguard.final.json'),'explicit_config_sha_and_bytes_required':True,'actual_config_pin':config_ref,'new_failure_origins':[],'native_Go_SQL_Git_model_executed':False,'STOP':True}
put('HDF.json',h)
print(json.dumps({'HDF':pin(N/'HDF.json'),'MF':pin(N/'MF.json'),'members':len(members),'serve':h['serve_ref'],'api':h['api_ref'],'preparer':h['preparer_ref']}))
