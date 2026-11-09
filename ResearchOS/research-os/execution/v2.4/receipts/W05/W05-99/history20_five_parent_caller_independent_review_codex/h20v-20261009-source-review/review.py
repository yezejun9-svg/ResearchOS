import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,ast,re,types
P=pathlib.Path;N=P(__file__).resolve().parent;B=N.parent.parent;R=B.parents[4]
C=B/'integration_codex/history20-five-parent-sparse-root-source-h20v-1a11ebe661670a1a49d0ea22092604a'
checks=[];inputs={}
def ck(name,value):checks.append(dict(name=name,passed=bool(value)))
def pin(p):
 p=P(p).resolve();r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def verify(v):
 x=dict(path=str(P(v['path']).resolve()),sha256=v['sha256'].removeprefix('sha256:'),bytes=v['bytes']);a=pin(x['path']);ck('exact:'+a['path'],a==x)
 key=x['path'].casefold();ck('consistent:'+x['path'],key not in inputs or inputs[key]==x);inputs[key]=x
 return x
def add(p):return verify(pin(p))
def fixed(p,h,z):return verify(dict(path=str(p),sha256=h,bytes=z))
def read(p):return json.loads(P(p).read_bytes())
def mem(ref):
 verify(ref);m=read(ref['path'])['members'];return list(m.values()) if isinstance(m,dict) else m
def save(n,v):
 with (N/n).open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
 return pin(N/n)
fixed(C/'HDF.json','fcc6de7fc2696474764cf8c2b27f9cfcd7942179bf5cdf6a589cf13ac45f4c76',3189)
fixed(C/'MF.json','39e8c747edc6f4f323f1842190edfe32b04ea45cacc3ebd73b7d1443882a0b1b',4962)
h=read(C/'HDF.json')
for v in mem(h['manifest_ref']):verify(v)
for k in ('prepare_ref','validate_ref','choice_ref','composition_ref','static_ref','guard_ref','instructions_ref'):verify(h[k])
for v in read(C/'input-pins.json'):verify(v)
author_guard=read(h['guard_ref']['path'])
ck('author-pin-snapshot-no-canonical-guard',author_guard['before_after_unchanged'] and not author_guard['canonical_guards_held'] and not author_guard['Main_or_old_worktree_mutated'])
choice=read(h['choice_ref']['path']);composition=read(h['composition_ref']['path'])
ck('source-component-order',[x['component'] for x in choice['source_components']]==['ATT3','Q5','LEG2','EXPIRED','AF','H20R1'])
for v in choice['base_driver_refs']:verify(v)
verify(choice['actual_T11_overlay_ref']);verify(choice['actual_T11_closed_ref'])
ck('T11-overlay-ref-in-base-driver-list',choice['actual_T11_overlay_ref'] in choice['base_driver_refs'])
actual=read(choice['actual_T11_closed_ref']['path'])
ck('old-T11-actual-scope',actual['source_count']==58 and actual['pass_count']==5 and actual['fail_count']==actual['skip_count']==0 and actual['all_owned_jobs_closed'] and actual['Main_canonical_unchanged'])
old=read(choice['base_current49']);add(choice['base_current49']);verify(old['formatted_source_ref'])
ck('old49-known-partial-not-relabelled',old['source_count']==49 and old['pass_count']==61 and old['fail_count']==6 and old['skip_count']==0)
base_root=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
sources={P(v['path']).resolve().relative_to(base_root).as_posix():verify(v) for v in read(old['formatted_source_ref']['path'])}
ck('base49',len(sources)==49)
preserved=set(old['exact_25_parent_names']);before_h20={};h20={}
t11={k:verify(v) for k,v in read(choice['actual_T11_overlay_ref']['path'])['sources'].items()}
for item in choice['source_components']:
 for field in ('source_handoff','source_manifest','independent_handoff','independent_manifest'):verify(item[field])
 for v in mem(item['source_manifest'])+mem(item['independent_manifest']):verify(v)
 candidate=(B/item['candidate_namespace']/'candidate-root').resolve()
 if item['component']=='H20R1':
  before_h20=dict(sources);ck('actual58-equals-full-composition-before-H20',sources==t11 and len(sources)==58)
  ck('reuse-H20R1-independent-source-pass',read(item['independent_handoff']['path'])['status']=='SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME')
 for v in mem(item['source_manifest']):
  p=P(v['path']).resolve()
  if not p.is_relative_to(candidate):continue
  rel=p.relative_to(candidate).as_posix();sources[rel]=verify(v)
  if item['component']=='H20R1':h20[rel]=verify(v)
  if rel.endswith('_test.go'):preserved.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',p.read_text(encoding='utf-8'),re.M))
ck('five-exact-H20-paths',set(h20)==set(choice['h20_candidate_paths'])=={'internal/domain/backup.go','internal/domain/backup_upgrade.go','internal/domain/backup_history20_upgrade.go','internal/domain/backup_history20_upgrade_test.go','ops/backup/main.go'})
ck('actual61-composition',len(sources)==61 and sources==composition['final_sources'] and choice['expected_source_count']==61)
ck('two-overlays-plus-three-new-members',len(set(before_h20)&set(h20))==2 and len(set(h20)-set(before_h20))==3)
ck('two-production-overlays',set(before_h20)&set(h20)=={'internal/domain/backup.go','internal/domain/backup_upgrade.go'})
ck('ops-backup-repo-existing-new-overlay',(R/'ops/backup/main.go').is_file() and 'ops/backup/main.go' not in before_h20)
ck('AF-exact',sources['internal/domain/client_protocol_attach_contract_windows_test.go']==t11['internal/domain/client_protocol_attach_contract_windows_test.go'])
ck('every-non-H20-exact',all(sources[k]==v for k,v in before_h20.items() if k not in h20))
ck('59-parent-derived-preserved',len(preserved)==59 and preserved==set(choice['source_preserved_parent_names']))
declared=set()
for k,v in sources.items():
 if k.endswith('_test.go'):declared.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',P(v['path']).read_text(encoding='utf-8'),re.M))
ck('137-declared-source-only',len(declared)==137 and declared==set(choice['all_source_file_declared_parent_names']))
test=P(h20['internal/domain/backup_history20_upgrade_test.go']['path']).read_text(encoding='utf-8')
parents=set(re.findall(r'^func (TestHistory20[A-Za-z0-9_]+)\(',test,re.M))
drift=re.search(r'for _, tc := range \[\]string\{([^}]+)\}',test).group(1)
subcases=re.findall(r'"([^"]+)"',drift)
terminals=parents|{'TestHistory20RejectsReleaseAndSourceDrift/'+x for x in subcases}
ck('exact-five-parent-selector',len(parents)==5 and parents==set(choice['exact_parent_names']))
ck('exact-nine-terminals',len(terminals)==9 and terminals==set(choice['expected_terminal_names']) and subcases==['migration-hash','extra-numbered-migration','foreign-table','session-addon'])
ck('54-unselected-preserved',len(preserved-parents)==54 and choice['source_preserved_nonselected_parent_count']==54)
for key in ('fresh_worktree','fresh_isolation_output','fresh_validation_output','fresh_environment'):
 p=P(choice[key]);ck('fresh-absent:'+key,not p.exists());ck('fresh-in-repository:'+key,p.is_relative_to(R))
ck('fresh-four-distinct',len({str(P(choice[k]).resolve()).casefold() for k in ('fresh_worktree','fresh_isolation_output','fresh_validation_output','fresh_environment')})==4)
func_audits=[]
for change in read(C/'source-replacements.json'):
 verify(change['original']);verify(change['candidate'])
 oldraw=P(change['original']['path']).read_bytes();newraw=P(change['candidate']['path']).read_bytes()
 inverse=newraw.decode().replace('\r\n','\n')
 for before,after in reversed(change['replacements']):
  ck('inverse-present:'+P(change['candidate']['path']).name+':'+before,after in inverse);inverse=inverse.replace(after,before)
 newline='\r\n' if b'\r\n' in oldraw else '\n'
 ck('exact-byte-inverse:'+P(change['candidate']['path']).name,inverse.replace('\n',newline).encode()==oldraw)
 oldtree=ast.parse(oldraw);newtree=ast.parse(newraw)
 defs=lambda tree:{n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 olddefs,newdefs=defs(oldtree),defs(newtree)
 allowed={'closed'} if P(change['candidate']['path']).name.startswith('validate_') else set()
 ck('same-function-inventory:'+P(change['candidate']['path']).name,set(olddefs)==set(newdefs))
 for name in set(olddefs)-allowed:ck('function-unchanged:'+name,olddefs[name]==newdefs[name])
 func_audits.append(dict(candidate=change['candidate'],unchanged=sorted(set(olddefs)-allowed),allowed_metadata_function_changes=sorted(allowed)))
prep=P(h['prepare_ref']['path']).read_text(encoding='utf-8');val=P(h['validate_ref']['path']).read_text(encoding='utf-8')
baseprep=(C/'base/prepare_attach_fixture_two_parent.actual_owned.py').read_text(encoding='utf-8')
baseval=(C/'base/validate_attach_fixture_two_parent.actual_owned.py').read_text(encoding='utf-8')
for label,new,oldsource in [('preparer',prep,baseprep),('validator',val,baseval)]:
 ck('finally-preserved:'+label,new[new.rindex('finally:'):]==oldsource[oldsource.rindex('finally:'):])
ck('six-owned-Git-receipts','invocation_refs=[verify,tracked,staged,create,checkout,verify_after]' in prep and 'owned_jobs=6' in prep)
ck('no-shared-config-sparse-metadata','metadata.is_relative_to((R/".git/worktrees").resolve())' in prep and 'shared_git_config_mutated=False' in prep and '"read-tree","-mu","HEAD"' in prep)
ck('dirty-head-index-checks','len(tracked_lines)==13' in prep and 'sum(line.startswith(" D ") for line in tracked_lines)==11' in prep and 'not (O/"staged-status.stdout.raw").read_bytes().strip()' in prep and prep.count('==expected')>=2)
ck('dynamic-current-checkpoint-both','len(sys.argv)==4' in prep and 'len(sys.argv)==8' in val and 'checkpoint_revision' in prep and 'checkpoint_revision' in val)
ck('exact-isolation-pin-and-identity','"sha256":sys.argv[6],"bytes":int(sys.argv[7])' in val and 'isolation["source_overlay"] is False' in val and 'Path(isolation["worktree_root"]).resolve()==T' in val)
ck('five-validation-guards-finally','((binary_guard,"binary"),(compiler_guard,"compiler"),(candidate_guard,"candidate"),(runtime_guard,"runtime"),(input_guard,"input"))' in val)
ck('actual-full-list-compiler-embed','"-test","-deps","-compiled","-tags=researchos_native_recovery_harness","-json","./internal/domain"' in val and '"TestEmbedFiles","XTestEmbedFiles"' in val and 'compiler_guard.acquire(compiler_refs)' in val)
ck('tagged-full-domain-compile','"test","-c","-tags=researchos_native_recovery_harness","-trimpath","-buildvcs=false","-o",str(binary),"./internal/domain"' in val)
ck('official-test2json-binary-guard','dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c' in val and 'binary_guard.acquire([pin(binary),pin(test2json)])' in val)
ck('anchored-five-selector','selector="^("+("|".join(sorted(new_tests)))+")$"' in val and '"-test.run="+selector' in val)
ck('reject-other-top-level-tests','assert name.split("/",1)[0] in new_tests' in val)
ck('exact-unique-run-terminal','name not in starts' in val and 'name in starts and name not in actions' in val and 'starts==set(actions)==set(choice["expected_terminal_names"])' in val and 'len(actions)==9' in val)
ck('native-exit-pass-noskip-package-pass','result["actual_exit"]==0' in val and 'all(action=="pass" for action in actions.values())' in val and 'events[-1]["Action"]=="pass" and "Test" not in events[-1]' in val)
ck('bounded-tests14min-owned15min','"-test.timeout=14m"' in val and '],900,T/"internal/domain")' in val)
ck('new-worktree-only-overlay','path=T/relative' in val and 'path.write_bytes(input_guard.get_buffer(ref["path"]))' in val)
ck('closed-no-runtime-overclaim','nonselected_parents_executed_or_newly_accepted=False' in val and 'history20_scope="PUBLIC_FIXTURE_A20_TO_PLAIN21_ONLY"' in val and 'formal_acceptance=False' in val)
ck('native-harness-not-selected','TestNativeMigrationAuthorityHarness' not in parents)
# The ops CLI help file is copied/formatted/inventoried but domain-only compile does not compile that package.
ck('ops-CLI-scope-observed',h20['ops/backup/main.go']['bytes']==6420 and './ops/backup' not in val)
save('composition.audit.json',dict(sources=sources,derived_parent_names=sorted(preserved),declared_parent_names=sorted(declared),selected_parents=sorted(parents),expected_terminals=sorted(terminals),function_audits=func_audits,ops_cli_built_or_executed=False))
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
fixed(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85',11404)
raw=gp.read_bytes();m=types.ModuleType('h20v_review_guard');m.__file__=str(gp);sys.modules[m.__name__]=m;exec(compile(raw,str(gp),'exec'),m.__dict__)
add(__file__);add(sys.executable)
for mod in list(sys.modules.values()):
 for attr in ('__file__','__cached__'):
  p=getattr(mod,attr,None)
  if p and P(p).is_file():add(p)
canonical={str(R/'execution/v2.4'/name).casefold() for name in ('checkpoint.json','path_ownership.json','step_state.json','commands.json')}
ck('no-current-canonical-handle',not (set(inputs)&canonical))
guard=m.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
 guard.acquire(list(inputs.values()))
 for v in inputs.values():ck('final-unchanged:'+v['path'],pin(v['path'])==v)
finally:
 cleanup=guard.close();save('sourceguard.final.json',cleanup)
ck('guard-released',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
save('input-pins.json',list(inputs.values()))
save('checks.json',dict(checks=checks,passed=sum(v['passed'] for v in checks),failed=sum(not v['passed'] for v in checks),input_count=len(inputs)))
print(json.dumps(dict(check_count=len(checks),failed=[v for v in checks if not v['passed']],input_count=len(inputs),guard_closed=cleanup['closed'],actual_Git_Go_SQL_native_model=False),ensure_ascii=True))

