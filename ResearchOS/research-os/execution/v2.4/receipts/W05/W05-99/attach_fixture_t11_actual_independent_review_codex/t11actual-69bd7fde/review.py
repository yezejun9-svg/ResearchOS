import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,re,importlib.util,traceback,datetime
P=pathlib.Path;O=P(__file__).resolve().parent;R=P('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
I=B/'integration_codex/attach-fixture-two-parent-sparse-isolation-root-1791516205000'
A=B/'integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000'
S=B/'integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths'
V=B/'sparse_checkout_independent_review_codex/r2-1791516205000-84568553/retry-schema'
P0=B/'attach_fixture_two_parent_caller_independent_review_codex/t11r-20261009-source-review'
Q3=B/'integration_codex/typed-q3-epoch-targeted-root-0c4318e1c10443f2'
T9=B/'integration_codex/current-attach-q5-leg2-targeted-root-1791510290800'
T=R/'.local/worktrees/t11s-1791516205000';Told=R/'.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371'
F894=B/'integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/failure-origin.894.json'
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
refs={};provenance={};checks=[];g=None
def norm(r):return dict(path=str(P(r['path']).resolve()),sha256=r['sha256'].removeprefix('sha256:'),bytes=r['bytes'])
def pin(p):
 p=P(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def add(r,why):
 r=norm(r);k=r['path'].casefold()
 assert k not in refs or refs[k]==r,'conflicting exact references: '+r['path']
 refs[k]=r;provenance.setdefault(k,[]).append(why)
def rawrefs(v):
 if isinstance(v,dict):
  if {'path','sha256','bytes'}.issubset(v) and isinstance(v['path'],str) and isinstance(v['sha256'],str) and type(v['bytes']) is int:yield v
  else:
   for x in v.values():yield from rawrefs(x)
 elif isinstance(v,list):
  for x in v:yield from rawrefs(x)
def save(n,v):
 with (O/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def ck(n,v,d=None):checks.append(dict(check=n,passed=bool(v),detail=d))
def good(x):return x.get('schema')=='researchos.source-read-guard-observation.v1' and x['verification']=='PASSED' and x['closed'] and x['retained_handles_count']==0 and x['failure'] is None and not x['errors'] and all(e['verified'] and e['final_path_match'] and e['closed'] for e in x['entries'])
def entries(d):return {str(P(r['path']).resolve()).casefold():norm(r) for r in d['entries']}
def main():
 global g
 guardfiles=list(I.glob('*guard.cleanup.actual.json'))+list(A.glob('*guard.cleanup.actual.json'))
 for d in [I,A]:
  for p in d.iterdir():
   if p.is_file():add(pin(p),'actual-receipt')
 for p in guardfiles:
  for r in json.loads(p.read_bytes())['entries']:add(r,'historical-runtime-guard:'+p.name)
 for p in [S/'HDF.json',S/'MF.json',S/'postseal-root-actual-original-io.json',V/'HDF.json',V/'MF.json',P0/'HDF.json',P0/'MF.json',P0/'source-composition-reviewed.json',T9/'validation.closed.json',T9/'formatted.source-members.json',Q3/'validation.closed.json',F894,G,P(__file__)]:
  add(pin(p),'independent-review-support')
 for h in [json.loads((V/'HDF.json').read_bytes()),json.loads((S/'HDF.json').read_bytes())]:
  for r in rawrefs(h):
   # Source-only HDF has no changing historical canonical pointer.
   add(r,'source-review-HDF-binding')
 for r in json.loads((A/'formatted.source-members.json').read_bytes()):add(r,'formatted58')
 inventory0=json.loads((A/'actual-tagged-compiler-input-inventory.json').read_bytes())
 for r in rawrefs(inventory0):add(r,'actual-compiler-inventory')
 pattern0=json.loads((I/'sparse-checkout.patterns.public.json').read_bytes())
 add(pattern0['pattern_ref'],'actual-pattern-file');metadata=P(pattern0['metadata'])
 for p in [T/'.git',metadata/'gitdir',metadata/'HEAD']:add(pin(p),'worktree-metadata-read-only')
 oldI=P(json.loads(F894.read_bytes())['native_invocation_path']).parent
 for n in ['create-worktree.invocation.json','create-worktree.stderr.raw','tracked-status.stdout.raw','staged-status.stdout.raw','source-guard.cleanup.actual.json','runtime-source-guard.cleanup.actual.json']:add(pin(oldI/n),'failed894-preserved')
 assert pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
 spec=importlib.util.spec_from_file_location('t11_actual_review_guard',G);gm=importlib.util.module_from_spec(spec);spec.loader.exec_module(gm)
 g=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(list(refs.values()))
 def raw(p):return g.get_buffer(str(P(p).resolve()))
 def obj(p):return json.loads(raw(p))
 def verified(r):
  b=raw(r['path']);return hashlib.sha256(b).hexdigest()==r['sha256'].removeprefix('sha256:') and len(b)==r['bytes']
 def rp(p):
  p=P(p).resolve();b=raw(p);return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 def mapped(values):return {str(P(v['path']).resolve()).casefold():norm(v) for v in values}
 save('input-pins.json',list(refs.values()));save('reference-provenance.json',provenance)
 for r in refs.values():ck('input-exact:'+r['path'],verified(r))
 ready=obj(I/'isolation.ready.json');closed=obj(A/'validation.closed.json');io=obj(S/'postseal-root-actual-original-io.json')
 ck('isolation-ready-exact',rp(I/'isolation.ready.json')['sha256']=='9ba9e237b673febdb64a586fdecaac57aef93d726f3cb7ba27767d3a4934bbdc' and len(raw(I/'isolation.ready.json'))==4099)
 ck('validation-closed-exact',rp(A/'validation.closed.json')['sha256']=='06ef4ac9095dac2c95d9732163f6187da164cb6e3439b32a8a6d40379530bec2' and len(raw(A/'validation.closed.json'))==21659)
 ck('source-review-exact-and-pending-actual-only',rp(V/'HDF.json')['sha256']=='7f53347ae3e1a3389434144ccd308897b45e3c2411af08099fddcff84e02da48' and obj(V/'HDF.json')['status']=='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL' and obj(V/'HDF.json')['formal_acceptance'] is False)
 sourceH=obj(V/'HDF.json')
 for name in ['source_handoff','source_manifest','prepare_ref','validate_ref','choice_ref']:ck('Source-accepted-pin:'+name,verified(sourceH[name]))
 cpExpected='9e67531bd3b1f0fbd9bc5e239b3a240a39f668db2d367714a399ba4fd8bfeb25'
 ck('Root-launch-exact-source-and-CP-ready-arguments',P(io['isolation_call_input']['driver']).resolve()==P(sourceH['prepare_ref']['path']).resolve() and P(io['validation_call_input']['driver']).resolve()==P(sourceH['validate_ref']['path']).resolve() and io['isolation_call_input']['argv']==[cpExpected,'4223052','363'] and io['validation_call_input']['argv']==['44afd8c086194419cc2f6f12ba01916adb2f8846345c7989e3fe071d046f79fc','19864',cpExpected,'4223052','363','9ba9e237b673febdb64a586fdecaac57aef93d726f3cb7ba27767d3a4934bbdc','4099'])
 ck('Root-initial-session-and-final-exits',io['isolation_initial']['session_id']==24094 and io['isolation_initial']['chunk_id']=='27ca9b' and io['isolation_completion']['chunk_id']=='14da82' and io['validation_initial']['session_id']==71603 and io['validation_initial']['chunk_id']=='972b48' and io['validation_completion']['chunk_id']=='3623df' and io['explicit_python_exits']=={'isolation':0,'validation':0})
 progress={}
 for which in ['isolation','validation']:
  end=io[which+'_completion'];ck(which+':outer-Python-exit0',end['exit_code']==0 and end['output'].rstrip().endswith('ROOT_PYTHON_EXIT=0'))
  for part in ['initial','completion']:
   for line in io[which+'_'+part]['output'].splitlines():
    if not line.startswith('{'):continue
    j=json.loads(line)
    for r in rawrefs(j):ck(which+':original-stdout-ref-binding:'+P(r['path']).name,verified(r))
    if 'progress' in j:progress[j['progress']]=j
 expected=[(I,'head-before',85004,134359900063433841),(I,'tracked-status',1148,134359900064759150),(I,'staged-status',78436,134359900069372196),(I,'create-worktree',29708,134359900070656157),(I,'checkout-product-source',86916,134359900073534577),(I,'head-after',83772,134359900237853799),(A,'format',42816,134359900661878521),(A,'tagged-compiler-input-list',43792,134359900671070132),(A,'tagged-test-binary-compile',33008,134359901349333130),(A,'attach-fixture-current-two-parent-jsonl',12840,134359901651185821)]
 jobs=[];invs={}
 for d,name,pid,ft in expected:
  inv=obj(d/(name+'.invocation.json'));invs[name]=inv;r=inv['result'];j=r['job_cleanup']
  ck(name+':exact-PID-uint64-exit0',r['owned_child_pid']==pid and type(r['creation_time_100ns']) is int and r['creation_time_100ns']==ft and r['actual_exit']==0 and inv['actual_native_exit']==0 and r['resumed'] is True)
  ck(name+':owned-job-closed',r['timed_out'] is False and r['error'] is None and j['termination_requested'] is False and j['unassigned_suspended_child_termination_requested'] is False and j['active_processes_last_observed']==0 and all(j[k] for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and not j['errors'])
  ck(name+':raw-stream-bindings',verified(inv['stdout_ref']) and verified(inv['stderr_ref']))
  ck(name+':Root-raw-progress-binding',name in progress and norm(progress[name]['receipt_ref'])==rp(d/(name+'.invocation.json')))
  jobs.append(dict(name=name,pid=pid,creation_FILETIME_decimal=str(ft),actual_owned_process_exit=0,owned_process_executable=inv['argv'][0],job_cleanup=j,elapsed_seconds=r['elapsed_seconds']))
 ck('exact-ten-owned-invocations',len(ready['invocation_refs'])==6 and len(closed['invocation_refs'])==4 and set(progress)=={x[1] for x in expected})
 ck('ready-is-isolation-stage-not-current-no-overlay-claim',ready['source_overlay'] is False and ready['all_owned_jobs_closed'] is True and closed['source_overlay_ref'] is not None and closed['Main_adopted'] is False)
 create=invs['create-worktree']['argv'];checkout=invs['checkout-product-source']['argv']
 ck('actual-no-checkout-and-command-sparse-flags','--no-checkout' in create and '--detach' in create and str(T) in create and checkout[-3:]==['read-tree','-mu','HEAD'] and 'core.sparseCheckout=true' in checkout and 'core.sparseCheckoutCone=false' in checkout and checkout[1:3]==['-C',str(T)])
 pattern=obj(I/'sparse-checkout.patterns.public.json')
 gitpointer=raw(T/'.git').decode().strip()
 ck('actual-sparse-pattern-and-own-metadata',raw(pattern['pattern_ref']['path']).decode()==pattern['patterns'] and len(pattern['patterns'].splitlines())==20 and P(pattern['metadata']).resolve().is_relative_to((R/'.git/worktrees').resolve()) and gitpointer.startswith('gitdir: ') and P(gitpointer[8:]).resolve()==metadata.resolve() and P(raw(metadata/'gitdir').decode().strip()).resolve()==T/'.git' and raw(metadata/'HEAD').decode().strip()==ready['head'])
 ck('unneeded-historical-trees-absent',not (T/'execution/v2.4/receipts').exists() and not (T/'execution/verifier').exists() and (T/'execution/toolchains/locked.json').is_file())
 status=raw(I/'tracked-status.stdout.raw').decode().splitlines()
 ck('13-dirty11-deletions-before-isolation-preserved',status==ready['tracked_dirty_paths'] and len(status)==13 and sum(x.startswith(' D ') for x in status)==11 and raw(I/'tracked-status.stdout.raw')==raw(oldI/'tracked-status.stdout.raw'))
 ck('staged-empty-before-isolation-and-main-head-stable',raw(I/'staged-status.stdout.raw').strip()==b'' and raw(I/'staged-status.stdout.raw')==raw(oldI/'staged-status.stdout.raw') and raw(I/'head-before.stdout.raw').decode().strip()==raw(I/'head-after.stdout.raw').decode().strip()=='adc460c2138528f163f7fdab5e8d81dde157b7fb')
 guardsets={};guardfacts=[]
 for p in guardfiles:
  gg=obj(p);ck('historical-guard-closed:'+str(p),good(gg));guardsets[(p.parent.name,p.name)]=entries(gg);guardfacts.append(dict(path=str(p),entry_count=len(gg['entries']),verified_closed=good(gg)))
 expected_counts={I.name:{'source-guard.cleanup.actual.json':115,'runtime-source-guard.cleanup.actual.json':30},A.name:{'input-source-guard.cleanup.actual.json':951,'runtime-source-guard.cleanup.actual.json':29,'candidate-source-guard.cleanup.actual.json':59,'compiler-source-guard.cleanup.actual.json':3923,'binary-source-guard.cleanup.actual.json':2}}
 ck('all-seven-stage-guard-counts',{d:{p.name:len(obj(p)['entries']) for p in guardfiles if p.parent.name==d} for d in [I.name,A.name]}==expected_counts)
 for pre in [obj(I/'canonical.pre-run.exact.json'),obj(A/'canonical.pre-run.exact.json')]:
  ck('canonical-before-and-now-exact363',pre['revision']==363 and all(verified(r) for r in pre['refs']) and pre['refs'][0]['sha256']==cpExpected and pre['refs'][0]['bytes']==4223052)
  for r in pre['refs']:
   key=str(P(r['path']).resolve()).casefold()
   ck('canonical-held-through-actual:'+P(r['path']).name,guardsets[(I.name,'source-guard.cleanup.actual.json')].get(key)==norm(r) and guardsets[(A.name,'input-source-guard.cleanup.actual.json')].get(key)==norm(r))
 # Full compiler input reconstruction from the retained actual go-list JSON, not from hand-written counts.
 inv=obj(A/'actual-tagged-compiler-input-inventory.json');txt=raw(A/'tagged-compiler-input-list.stdout.raw').decode();decoder=json.JSONDecoder();pos=0;packages=[];build={};embeds=[]
 fields=('GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles')
 while pos<len(txt):
  while pos<len(txt) and txt[pos].isspace():pos+=1
  if pos==len(txt):break
  pkg,pos=decoder.raw_decode(txt,pos)
  ck('go-list-package-no-error:'+str(len(packages)),not pkg.get('Error') and not pkg.get('DepsErrors'))
  packages.append(pkg.get('ImportPath'))
  if not pkg.get('Dir'):continue
  directory=P(pkg['Dir'])
  for field in fields:
   for name in pkg.get(field,[]):
    p=P(name);p=p if p.is_absolute() else directory/p;r=rp(p);build[r['path'].casefold()]=r
    if field.endswith('EmbedFiles'):embeds.append(dict(package=pkg['ImportPath'],field=field,ref=r))
 ck('all352packages-reconstructed',packages==inv['packages'] and len(packages)==inv['package_count']==352 and pos==len(txt))
 ck('all3731-build-inputs-reconstructed',build==mapped(inv['build_inputs']) and len(build)==3731)
 ck('all39-embed-entries-reconstructed',embeds==inv['actual_embed_files'] and len(embeds)==39)
 product={}
 for relative in ['apps/control','internal','adapters','evaluation','ops','migrations/sqlite','spec/v2.0/contracts']:
  for p in (T/relative).rglob('*'):
   ck('no-product-symlink:'+str(p),not p.is_symlink())
   if p.is_file():r=rp(p);product[r['path'].casefold()]=r
 for relative in ['go.mod','go.sum','execution/toolchains/locked.json']:
  r=rp(T/relative);product[r['path'].casefold()]=r
 ck('all605-product-inputs-reconstructed',product==mapped(inv['product_inventory']) and len(product)==605)
 goroot=P(inv['GoRef']['path']).parent.parent
 tools=[rp(p) for p in (goroot/'pkg/tool/windows_amd64').iterdir() if p.is_file()]
 ck('all8-compiler-tools-reconstructed',mapped(tools)==mapped(inv['compiler_tool_refs']) and len(tools)==8)
 compiler=dict(build);compiler.update(product);compiler.update(mapped(tools));compiler.update(mapped([inv['GoRef'],closed['compiler_inventory_ref']]))
 ck('compiler-guard-exact-full-union3923',compiler==guardsets[(A.name,'compiler-source-guard.cleanup.actual.json')] and len(compiler)==3923)
 ck('compile-real-exact-tagged-source-and-binary',invs['tagged-test-binary-compile']['argv'][1:]==['test','-c','-tags=researchos_native_recovery_harness','-trimpath','-buildvcs=false','-o',closed['compiled_test_ref']['path'],'./internal/domain'] and P(invs['tagged-test-binary-compile']['cwd']).resolve()==T and verified(closed['compiled_test_ref']))
 ck('official-test2json-pinned-binaryguard',inv['test2json_executable_ref']['sha256']=='dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c' and guardsets[(A.name,'binary-source-guard.cleanup.actual.json')]==mapped([closed['compiled_test_ref'],inv['test2json_executable_ref']]))
 # Source composition and delta from the actual T9 formatted manifest.
 formatted=obj(A/'formatted.source-members.json');source=obj(A/'source-overlay.json');composition=obj(P0/'source-composition-reviewed.json')
 ck('source-composition-exact-approved58',source['sources']==composition['sources'] and source['Source_count']==closed['source_count']==58 and source['Main_adopted'] is False)
 fnew={P(r['path']).resolve().relative_to(T).as_posix():norm(r) for r in formatted}
 oldclosed=obj(T9/'validation.closed.json');fold={P(r['path']).resolve().relative_to(Told).as_posix():norm(r) for r in obj(T9/'formatted.source-members.json')}
 ck('58-current-formatted-files-and-candidate-guard',len(fnew)==58 and set(fnew)==set(source['sources']) and guardsets[(A.name,'candidate-source-guard.cleanup.actual.json')]==mapped(formatted+[closed['formatted_source_ref']]))
 changed=[k for k in fnew if k not in fold or (fnew[k]['sha256'],fnew[k]['bytes'])!=(fold[k]['sha256'],fold[k]['bytes'])]
 ck('only-AF-source-delta-vs-actualT9',fnew.keys()==fold.keys() and changed==['internal/domain/client_protocol_attach_contract_windows_test.go'],changed)
 declarations=sorted(set(n for p in fnew if p.endswith('_test.go') for n in re.findall(r'^func (Test[A-Za-z0-9_]+)\(',raw(T/p).decode(),re.M)))
 ck('132-declarations-preserved-not-executed',declarations==composition['declarations'] and len(declarations)==132)
 choice=obj(S/'source.integration.choice.json')
 selected=set(choice['exact_parent_names'])
 ck('54-preserved2-selected52-unselected',selected==set(closed['exact_parent_names'])==set(composition['selected']) and set(closed['preserved_parent_source_names'])==set(composition['preserved_parents']) and len(closed['preserved_parent_source_names'])==54 and set(closed['nonselected_parent_sources'])==set(composition['nonselected']) and len(closed['nonselected_parent_sources'])==52)
 # Full test2json stream state machine: every named output/run/end is bound to the same selected package.
 testinv=invs['attach-fixture-current-two-parent-jsonl'];expectedargv=[inv['test2json_executable_ref']['path'],'-p','researchos.local/research-os/internal/domain','-t',closed['compiled_test_ref']['path'],'-test.v=test2json','-test.run=^('+'|'.join(sorted(selected))+')$','-test.count=1','-test.timeout=14m']
 ck('exact-official-test2json-selector-cwd',testinv['argv']==expectedargv and P(testinv['cwd']).resolve()==T/'internal/domain')
 events=[json.loads(line) for line in raw(A/'attach-fixture-current-two-parent-jsonl.stdout.raw').decode().splitlines()]
 runs={};ends={};times=[];pkg='researchos.local/research-os/internal/domain'
 for idx,e in enumerate(events):
  ck('event-package:'+str(idx),e['Package']==pkg);times.append(datetime.datetime.fromisoformat(e['Time']))
  name=e.get('Test');action=e['Action']
  if name:
   ck('event-selected-parent:'+str(idx),name.split('/',1)[0] in selected)
   if action=='run':
    ck('unique-run:'+name,name not in runs and name not in ends)
    if '/' in name:ck('leaf-parent-already-running:'+name,name.split('/',1)[0] in runs and name.split('/',1)[0] not in ends)
    runs[name]=idx
   elif action in ['pass','fail','skip']:
    ck('single-terminal-after-run:'+name,name in runs and name not in ends and runs[name]<idx)
    if '/' not in name:ck('parent-after-started-children:'+name,all(n in ends for n in runs if n.startswith(name+'/')))
    ends[name]=dict(action=action,index=idx)
   else:ck('named-output-while-running:'+str(idx),action=='output' and name in runs and name not in ends)
 expectednames=selected|{'TestClientAttachSettledAcquisitionCompletesAndReplays/'+x for x in ['unowned','expired-same-owner','other-client']}
 ck('exact-five-tests-complete',set(runs)==set(ends)==expectednames and all(v['action']=='pass' for v in ends.values()) and len(events)==23)
 ck('single-package-start-and-end',events[0]['Action']=='start' and 'Test' not in events[0] and events[-1]['Action']=='pass' and 'Test' not in events[-1] and sum(e['Action']=='start' for e in events)==1 and sum(e['Action'] in ['pass','fail','skip'] and 'Test' not in e for e in events)==1 and times==sorted(times))
 ck('closed-case-counts-and-actions-exact',closed['actions']=={k:v['action'] for k,v in ends.items()} and set(closed['started_names'])==set(runs) and closed['pass_count']==5 and closed['fail_count']==closed['skip_count']==0 and raw(A/'attach-fixture-current-two-parent-jsonl.stderr.raw')==b'')
 ck('Main-protected-files-exact-vs-runtime-inputguard',all(str((R/n).resolve()).casefold() in guardsets[(A.name,'input-source-guard.cleanup.actual.json')] and verified(guardsets[(A.name,'input-source-guard.cleanup.actual.json')][str((R/n).resolve()).casefold()]) for n in ['go.mod','go.sum','internal/domain/client_workspace_test.go','internal/domain/client_protocol_goal_test.go','internal/domain/runtime_permission_windows_test.go','internal/domain/runtime_tool_integration_windows_test.go','internal/domain/runtime_session_events_windows_test.go','internal/domain/store.go']))
 # Prior failures remain history. This fresh targeted pass does not rerun them.
 q3=obj(Q3/'validation.closed.json');fail894=obj(F894);inv894=obj(oldI/'create-worktree.invocation.json')
 ck('olderQ3-six-runtime-failures-not-reclassified',q3['pass_count']==61 and q3['fail_count']==6 and q3['formal_acceptance'] is False and not set(k for k,v in q3['actions'].items() if v=='fail').intersection(runs))
 ck('currentT9-152pass5fail-preserved',oldclosed['pass_count']==152 and oldclosed['fail_count']==5 and oldclosed['skip_count']==0 and oldclosed['formal_acceptance'] is False)
 ck('894-original-ENOSPC-Git128-preserved',fail894['ordinal']==894 and fail894['actual_outer_exit']==fail894['actual_python_exit']==1 and fail894['actual_native_exit']==inv894['result']['actual_exit']==128 and bool(re.search('no space left',raw(oldI/'create-worktree.stderr.raw').decode(),re.I)))
 cp=obj(R/'execution/v2.4/checkpoint.json')
 ck('no-Main-adoption-formal-or-full-scope-upgrade',closed['Main_adopted'] is False and closed['Main_canonical_unchanged'] is True and closed['nonselected_parents_executed_or_newly_accepted'] is False and closed['ordinary_history20_full_release_program_rehearsal_authority']=='BLOCKED' and closed['formal_acceptance'] is False and cp['revision']==363 and cp['current_effective_formal_status']['formal_cases_accepted']==0)
 save('owned-process-facts.json',{'jobs':jobs,'test_binary_process_identity_separately_recorded':False,'test_execution_wrapper':'official test2json.exe primary owned process; test binary is its job-contained descendant','actual_invocations':10})
 save('historical-guard-facts.json',guardfacts)
 save('inventory-reconstruction.json',{'packages':len(packages),'build_inputs':len(build),'product_inventory':len(product),'compiler_tools':len(tools),'embed_entries':len(embeds),'distinct_embed_files':len({x['ref']['path'] for x in embeds}),'compiler_guard_exact_union':len(compiler),'source_files':len(fnew),'T9_unchanged_formatted_files':len(fnew)-len(changed),'changed_from_T9':changed,'source_declarations':len(declarations),'selected_parents':sorted(selected),'nonselected_parent_count':52,'test_event_count':len(events),'terminal_tests':ends,'package_final_pass':True,'Main_Git_status_evidence_scope':'13 tracked dirty paths,11 deletions,empty staged output observed before isolated setup and identical to earlier894 baseline; no post-validation Git command rerun by reviewer.'})
 closure=g.close();save('guard.final.json',closure);ck('review-all-handles-closed',good(closure))
 result={'schema':'researchos.independent-T11-actual-closure-review.v1','decision':'T11_TWO_PARENT_ACTUAL_COMPONENT_ACCEPTED_NO_FORMAL_AUTHORITY' if all(x['passed'] for x in checks) else 'T11_ACTUAL_REVIEW_FINDINGS','checks':checks,'remaining_findings':[x for x in checks if not x['passed']],'guarded_input_count':len(refs),'guarded_input_bytes':sum(r['bytes'] for r in refs.values()),'actual_selected_parents':2,'actual_leaf_tests':3,'actual_pass_terminals':5,'actual_fail_terminals':0,'actual_skip_terminals':0,'other52_executed_or_newly_accepted':False,'Main_adopted':False,'formal_acceptance':False,'current_formal_count':0,'required_formal_count':42,'new_reviewer_execution_failures':0,'Git_Go_SQL_native_model_rerun_by_reviewer':False,'global_provider_request_count':None,'original_trial_provider_request_count':None,'authority':'ACTUAL_COMPONENT_EVIDENCE_ONLY','stop':True}
 save('review.json',result)
 print(json.dumps({k:result[k] for k in ['decision','remaining_findings','guarded_input_count','guarded_input_bytes','actual_selected_parents','actual_leaf_tests','actual_pass_terminals','new_reviewer_execution_failures','stop']}|{'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'all_guards_closed':closure['closed']},ensure_ascii=False))
code=0
try:main()
except Exception:traceback.print_exc();code=1
finally:
 if g is not None:
  closure=g.close()
  if not (O/'guard.final.json').exists():save('guard.final.json',closure)
 print('ROOT_PYTHON_EXIT='+str(code))
sys.exit(code)

