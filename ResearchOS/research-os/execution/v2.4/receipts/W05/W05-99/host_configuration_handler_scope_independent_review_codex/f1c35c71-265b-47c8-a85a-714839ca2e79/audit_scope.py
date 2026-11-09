import json,hashlib,pathlib,datetime,subprocess
ROOT=pathlib.Path.cwd()
OUT=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_scope_independent_review_codex/f1c35c71-265b-47c8-a85a-714839ca2e79'
P=ROOT/'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_scope_revision_codex/9d25ab2729444d0e96267dbc9c502430'
def sha(b): return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes(); return {'path':p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p),'sha256':sha(b),'bytes':len(b)}
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def write(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
proposal=read(P/'scope_proposal.json'); manifest=read(P/'manifest.final.json'); before=read(P/'input.before.json'); after=read(P/'input.after.json')
errors=[]; verified=[]
for r in manifest['files']:
 a=ref(ROOT/r['path']); verified.append(a)
 if a['sha256']!=r['sha256'] or a['bytes']!=r['bytes']: errors.append({'manifest_mismatch':r,'actual':a})
inputs=[]
for r in before['entries']:
 a=ref(pathlib.Path(r['original_absolute'])); s=ref(ROOT/r['snapshot_ref']['path']); inputs.append({'expected':r,'current':a,'snapshot_actual':s})
 if a['sha256']!=r['sha256'] or s['sha256']!=r['sha256']: errors.append({'input_mismatch':r['path']})
scope=[]
for r in proposal['exact_scope']:
 p=ROOT/r['path']; a=ref(p) if p.exists() else None
 scope.append({'path':r['path'],'action':r['action'],'current':a,'expected_absent':r['expected_absent'],'allowed_function_boundaries':r['allowed_function_boundaries']})
 if r['expected_absent'] and a is not None: errors.append({'new_path_exists':r['path']})
 if not r['expected_absent'] and (not a or a['sha256']!=r['source_before']['sha256']): errors.append({'scope_changed':r['path']})
refs=[];locators=[]
def walk(v):
 if isinstance(v,dict):
  if all(k in v for k in ('path','sha256','bytes')):
   p=ROOT/v['path']
   if p.is_file():
    a=ref(p);refs.append(a)
    if a['sha256']!=v['sha256'] or a['bytes']!=v['bytes']: errors.append({'reference_mismatch':v,'actual':a})
    if 'locator' in v:
     lines=v['locator'].get('lines',[]); count=len(p.read_text(encoding='utf-8-sig').splitlines());locators.append({'path':v['path'],'lines':lines,'line_count':count})
     if lines and not (1<=lines[0]<=lines[-1]<=count): errors.append({'bad_locator':v})
   else: errors.append({'missing_ref':v})
  for q in v.values(): walk(q)
 elif isinstance(v,list):
  for q in v:walk(q)
for n in ['scope_proposal.json','case_matrix30.json','potential_test_impacts.json']:walk(read(P/n))
head=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
# Immutable public inspection evidence. Existing author's byte snapshots remain the referenced originals.
public=['internal/api/v2_sessions_test.go','internal/host/host.go','internal/host/private_other.go','internal/domain/client_protocol.go','internal/domain/client_protocol_sessions.go','internal/domain/client_command_identity.go','internal/domain/client_protocol_atomic_test.go','internal/domain/client_transcript_test.go','internal/domain/client_workspace_test.go','internal/domain/runtime_tool_integration_windows_test.go','internal/domain/client_protocol_control_windows_test.go','internal/domain/client_command_queue_test.go','internal/domain/runtime_permission_windows_test.go','internal/domain/runtime_model_windows_test.go','internal/domain/runtime_sessions_windows_test.go','internal/domain/workbench_mixed_events_test.go','internal/domain/backup_host_configuration.go','internal/domain/client_configuration_test.go']
reads=[]
for name in public:
 p=ROOT/name;q=OUT/'actual_reads'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());reads.append({'original':ref(p),'snapshot':ref(q)})
write('actual_read_hash_audit.json',{'schema':'researchos.independent-static-audit.v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'proposal':ref(P/'scope_proposal.json'),'manifest':ref(P/'manifest.final.json'),'manifest_entry_count':len(verified),'manifest_entries':verified,'input_count':len(inputs),'inputs':inputs,'scope_count':len(scope),'scope':scope,'recursive_reference_count':len(refs),'recursive_refs':refs,'locator_count':len(locators),'locators':locators,'static_actual_reads':reads,'errors':errors,'test_sql_http_model_calls':0})
print(json.dumps({'head':head,'manifest_entries':len(verified),'inputs':len(inputs),'scope':len(scope),'refs':len(refs),'locators':len(locators),'errors':errors},ensure_ascii=False))
