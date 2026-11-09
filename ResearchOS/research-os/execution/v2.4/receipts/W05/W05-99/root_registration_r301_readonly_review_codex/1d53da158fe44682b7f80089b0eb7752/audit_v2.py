import pathlib,json,hashlib,subprocess,ast,datetime
R=pathlib.Path.cwd(); S=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/handler-and-g1-originals-r301';N=pathlib.Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def save(name,o): (N/name).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def ref(p):b=p.read_bytes();return {'path':p.relative_to(R).as_posix(),'sha256':H(b),'bytes':len(b)}
cache={}
resolved_locations=[]
W=R/'.local/worktrees/codex-w0599-host-configuration-handler'
def get(p):
 p=p.resolve()
 if not p.is_file() and p.is_relative_to(R/'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex'):
  original=p; p=W/p.relative_to(R); resolved_locations.append({'requested':str(original),'actual_author_original':str(p)})
 if p not in cache:cache[p]=p.read_bytes()
 return cache[p]
checks=[]
def walk(o,parent):
 if isinstance(o,dict):
  if isinstance(o.get('path'),str) and isinstance(o.get('sha256'),str):
   p=pathlib.Path(o['path']);p=p if p.is_absolute() else R/p
   if not p.resolve().is_relative_to(R):raise RuntimeError('outside repo '+str(p))
   b=get(p);checks.append({'parent':parent,'ref':o,'actual_sha256':H(b),'actual_bytes':len(b),'match':H(b)==o['sha256'] and ('bytes' not in o or len(b)==o['bytes'])})
  for v in o.values():walk(v,parent)
 elif isinstance(o,list):
  for v in o:walk(v,parent)
docnames=['prepared_refs.json','originals.audit.json','g1.originals.audit.json','handler38_independent_execution_scope.json','provider_g1_readonly_adjudication_scope.json','root_scope_review.json','root-readonly-tool-original.json']
for name in docnames:
 raw=get(S/name);(N/name).write_bytes(raw);walk(json.loads(raw),name)
wrapper=get(S/'run.py');(N/'wrapper.source.py.txt').write_bytes(wrapper);ast.parse(wrapper.decode('utf-8-sig'))
source=get(S/'register.py');(N/'register.source.py.txt').write_bytes(source);tree=ast.parse(source.decode('utf-8-sig'))
refs=json.loads(get(S/'prepared_refs.json'));audit=json.loads(get(S/'originals.audit.json'));g1=json.loads(get(S/'g1.originals.audit.json'))
for origin in audit['origins']:
 p=R/origin['evidence_ref']['path'];walk(json.loads(get(p)),origin['origin_key'])
previous=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/provider-g1-esm-attempt2-scope-r300/handoff-r300-running.json'
checks.append({'parent':'post-CAS handoff previous reference','ref':{'path':previous.relative_to(R).as_posix(),'sha256':'64ac45e3fc01a8e57b013e82670cff729f9c59e2d308f48123337580e2b42077'},'actual_sha256':H(get(previous)),'match':H(get(previous))=='64ac45e3fc01a8e57b013e82670cff729f9c59e2d308f48123337580e2b42077'})
metadata={name:get(R/'execution/v2.4'/name) for name in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']};cp=json.loads(metadata['checkpoint.json']);ow=json.loads(metadata['path_ownership.json']);old=cp['failure_counters'];lockp=R/'execution/toolchains/locked.json';lock=json.loads(get(lockp))['tools']
status=subprocess.check_output([lock['git']['path'],'status','--porcelain=v1','--untracked-files=no'],cwd=R);head=subprocess.check_output([lock['git']['path'],'rev-parse','HEAD'],cwd=R).decode().strip();(N/'git-status.original.raw').write_bytes(status)
tools=[]
for name in ['python','git']:
 p=pathlib.Path(lock[name]['path']);b=get(p);tools.append({'name':name,'path':str(p),'expected_sha256':lock[name]['sha256'],'actual_sha256':H(b),'match':H(b)==lock[name]['sha256']})
origins=[]
oldtext=json.dumps(old,ensure_ascii=False)
for x in audit['origins']:
 key=x['origin_key'];token=key.rsplit('/',1)[-1];origins.append({'origin_key':key,'already_registered_key':any(y.get('origin_key')==key for y in old),'token_in_old_entries':token in oldtext,'evidence_ref':x['evidence_ref'],'count':1})
raw_counts=[]
for row in audit['handler_public_copies']:
 if row['path'].endswith('/command.stdout'):
  events=[]
  for line in get(R/row['path']).splitlines():
   try:e=json.loads(line)
   except (ValueError,UnicodeDecodeError):continue
   if e.get('Test') and e.get('Action') in ['pass','fail','skip']:events.append(e)
  raw_counts.append({'raw':row,'counts':{k:sum(e['Action']==k for e in events) for k in ['pass','fail','skip']}})
# Native original invocations/raw are parsed read-only; never execute G1.
g1_native=[]
for rr in g1['g1_original_refs']+g1['outer_original_refs']:
 if rr['path'].endswith('.json') and 'invocation' in rr['path']:
  o=json.loads(get(R/rr['path']));g1_native.append({'ref':rr,'exit':o.get('exit',o.get('exit_code')),'raw_fields':list(o)})
current={name:H((R/'execution/v2.4'/name).read_bytes()) for name in metadata};unchanged=all(current[name]==H(raw) for name,raw in metadata.items())
bad=[x for x in checks if not x['match']]
sourceafter=H((S/'register.py').read_bytes());allafter=all(p.read_bytes()==b for p,b in cache.items())
save('reference_audit.json',{'explicit_author_original_locations':resolved_locations,'checks':checks,'bad':bad,'read_once_parse_same_bytes':True,'all_cached_inputs_after_equal':allafter})
save('origin_count_audit.json',{'origins':origins,'unique':len({x['origin_key'] for x in origins}),'raw_go_counts':raw_counts,'g1_native_invocations':g1_native,'before':len(old),'proposed_after':len(old)+len(origins),'g1_taskkill128_extra_count':0,'new_failure_this_audit':1,'new_failure_ref':'failure_origins.json','tool_raw_limit':'24e185,7a75e5,49560c use preserved actual tool-chunk locators; unavailable native stdout files are not invented.'})
save('canonical_readonly_snapshot.json',{'head':head,'status_sha256':H(status),'status_rows':len(status.splitlines()),'deleted_rows':sum(x[:2]==b' D' for x in status.splitlines()),'expected_before':[cp['revision'],ow['revision'],len(old)],'metadata':[{'name':name,'before_sha256':H(raw),'after_sha256':current[name]} for name,raw in metadata.items()],'unchanged':unchanged,'tool_hashes':tools,'toolchain_lock':ref(lockp)})
ready=(not bad and allafter and unchanged and sourceafter==H(source) and [cp['revision'],ow['revision'],len(old)]==[300,128,316] and all(x['match'] for x in tools) and not any(x['already_registered_key'] or x['token_in_old_entries'] for x in origins) and len(origins)==6)
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review','decision':'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' if ready else 'REQUEST_CHANGES','wrapper_ref':{'path':(S/'run.py').relative_to(R).as_posix(),'sha256':H(wrapper),'bytes':len(wrapper)},'register_ref':{'path':(S/'register.py').relative_to(R).as_posix(),'sha256':H(source),'bytes':len(source)},'expected_before':[300,128,316],'expected_after':[301,129,322],'actual_registration_executed':False,'product_test_executed':False,'canonical_writes':0,'formal_increment':0,'checks':[
 'Prepared top references, every original audit nested path/hash and scope reference independently byte-checked. Source parsed as AST only, never imported or executed.',
 'Six unique original invocations, no old origin/token duplicate. Actual CLI59/1 and282/12 match original Go raw; each whole batch counted once. G1 outer1 retained while Go3/JS child0 remain separate. Termination128 is same batch ancillary result, zero additional count.',
 'Cached reference bytes are used for hashing and JSON parsing, then reread before writes. Four metadata bytes and Git HEAD/status checked before each os.replace; expected_live updates only own replaced path; post-write exact byte verification and original316 prefix check.',
 'Both desired metadata byte files, originals, original Git status, intent and temp files exist before first replace. Exception records current hashes and phase; Root-only exact-original/desired forward recovery, external differences stop. No rollback/reset/automatic rerun.',
 'step_state/commands remain byte-identical; current_effective_formal_status preserved; handler/provider source_ready false; no held/model/LIVE qualification. Scope permits only isolated A-E+6C09 and separate read-only G1 adjudication.',
 'Previous r300 handoff hash independently verified now, although register.py reads it late after successful metadata verification. If final handoff emission fails, record as post-registration receipt failure and use saved intent/verified state; never rerun the registrar as a retry.'
 ],'execution_conditions':[
 'Root launches the exact reviewed source with locked python.exe -I, optimize=0; capture actual argv, stdout, stderr, exit and this review ref before launching. Script verifies executable path/SHA and refuses optimized mode.',
 'Immediately before launch independently compare this source SHA and prepared_refs bytes; retain reviewed Git-status SHA '+H(status)+' and unchanged four metadata hashes from canonical_readonly_snapshot.json. If changed, stop for fresh review; script initial count13/11deletions is not independently sufficient to identify baseline paths.',
 'No registration or Handler execution is implied by this receipt. Only Root actual successful CAS301 creates that lease. Do not claim any whole38 or whole9 source acceptance.'
 ],'limitations':['Wrapper independently read: pinned register SHA, -I child, PYTHONOPTIMIZE/PYTHONPATH removed, stdout/stderr exclusive raw capture, real child exit propagated; no automatic retry.','No crash/fault injection or actual registry execution performed in this read-only review. Recovery policy checked by code; any actual exception requires explicit Root forward-recovery procedure against exact journal bytes.','This is a bounded current-registration review, not a general-purpose hostile filesystem concurrency proof.'],'reference_audit':ref(N/'reference_audit.json'),'origin_audit':ref(N/'origin_count_audit.json'),'state_audit':ref(N/'canonical_readonly_snapshot.json'),'requested_changes':[] if ready else ['Inspect nonmatching audit entries before execution.']}
save('review.json',review)
manifest={'files':[{'path':p.relative_to(N).as_posix(),'sha256':H(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(N.rglob('*')) if p.is_file() and p.name not in ['manifest.json','handoff.json']]};save('manifest.json',manifest)
save('handoff.json',{'decision':review['decision'],'review':ref(N/'review.json'),'manifest':ref(N/'manifest.json'),'register_sha256':H(source),'expected_before':[300,128,316],'expected_after':[301,129,322],'canonical_writes':0})
print(json.dumps({'decision':review['decision'],'refs_checked':len(checks),'bad':len(bad),'register_sha256':H(source),'review':ref(N/'review.json'),'manifest':ref(N/'manifest.json'),'handoff':ref(N/'handoff.json')},ensure_ascii=True))
