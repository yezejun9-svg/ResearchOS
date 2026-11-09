from pathlib import Path
import ast,hashlib,json,re
N=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99'
BASE=B/'integration_codex/attach-fixture-two-parent-sparse-root-source-1791516205000/revision-exact-paths'
ACT=B/'integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000'
H=B/'historical20_upgrade_source_codex/h20-r1-root-1791519270000-scoped-check'
V=B/'historical20_upgrade_source_independent_review_codex/h20r1-20261009-source-review'
T=R/'.local/worktrees/h20s-1a11ebe6616'
ISO=B/'integration_codex/history20-five-parent-sparse-isolation-root-h20v-1a11ebe6616'
OUT=B/'integration_codex/history20-five-parent-sparse-target-root-h20v-1a11ebe6616'
ENV=R/'.local/history20-five-parent-env-1a11ebe6616'
inputs={}
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def use(p,sha=None,size=None):
 ref=pin(p)
 if sha is not None:assert ref['sha256']==sha,(str(p),'SHA mismatch')
 if size is not None:assert ref['bytes']==size,(str(p),'length mismatch')
 key=ref['path'].casefold();assert key not in inputs or inputs[key]==ref
 inputs[key]=ref;return ref
def verify(ref):return use(ref['path'],ref['sha256'].removeprefix('sha256:'),ref['bytes'])
def read(p):
 use(p);return json.loads(Path(p).read_text(encoding='utf-8'))
def members(ref):
 verify(ref);obj=read(ref['path']);v=obj['members'];return list(v.values()) if isinstance(v,dict) else v
def put(name,value):
 (N/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for p in [T,ISO,OUT,ENV]:assert not p.exists(),str(p)
hp=use(H/'HDF.json','08d1b809b51f4d246c4b272dba3d7e1bad9c9d3090b52f3464d635a8e18e49de',4294)
hm=use(H/'MF.json','c46bbdb08c3cec2c29fd04b135e466c3326ed7a7d68edd383051b3de72afe790',3777)
vp=use(V/'HDF.json','beea13c78af2a7ce8eb2e27fb043509be867f69adbd61de1ce3505cddebaba02',2566)
vm=use(V/'MF.json','cbe474017cdec7a472d84cded9f5fc72f2cd422b7bf29b1c6eb322220a6534d5',2283)
for ref in members(hm)+members(vm):verify(ref)
assert read(V/'HDF.json')['status']=='SOURCE_ACCEPTED_PENDING_ROOT_RUNTIME'
prep=BASE/'prepare_attach_fixture_two_parent.actual_owned.py'
val=BASE/'validate_attach_fixture_two_parent.actual_owned.py'
use(prep,'62fd1a7a3e947a4a922e4b36b31913ab215ed25e38abf708bba7105e74e93647',8806)
for p in [val,BASE/'HDF.json',BASE/'MF.json',BASE/'source.integration.choice.json']:use(p)
for ref in members(use(BASE/'MF.json')):verify(ref)
choice=read(BASE/'source.integration.choice.json')
act=read(ACT/'validation.closed.json')
assert act['source_count']==58 and act['pass_count']==5 and act['fail_count']==0 and act['skip_count']==0
assert act['all_owned_jobs_closed'] is True and act['Main_canonical_unchanged'] is True
actual_overlay_ref=verify(act['source_overlay_ref']);actual_overlay=read(actual_overlay_ref['path'])
actual_sources={k:verify(v) for k,v in actual_overlay['sources'].items()}
assert len(actual_sources)==58
old=read(choice['base_current49'])
assert old['source_count']==49
verify(old['formatted_source_ref'])
parent=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1')
sources={Path(p['path']).resolve().relative_to(parent).as_posix():verify(p) for p in read(old['formatted_source_ref']['path'])}
preserved=set(old['exact_25_parent_names'])
for item in choice['source_components']:
 for field in ['source_handoff','source_manifest','independent_handoff','independent_manifest']:verify(item[field])
 for ref in members(item['source_manifest'])+members(item['independent_manifest']):verify(ref)
 candidate=(B/item['candidate_namespace']/'candidate-root').resolve()
 for ref in members(item['source_manifest']):
  p=Path(ref['path']).resolve()
  if p.is_relative_to(candidate):
   rel=p.relative_to(candidate).as_posix();sources[rel]=verify(ref)
   if rel.endswith('_test.go'):preserved.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',p.read_text(encoding='utf-8'),re.M))
assert sources==actual_sources,'actual T11 overlay differs from composed old Source'
assert preserved==set(choice['source_preserved_parent_names'])
old_sources=dict(sources);old_preserved=set(preserved)
expected_h20={'internal/domain/backup.go','internal/domain/backup_upgrade.go','internal/domain/backup_history20_upgrade.go','internal/domain/backup_history20_upgrade_test.go','ops/backup/main.go'}
h20sources={}
for ref in members(hm):
 p=Path(ref['path']).resolve()
 if p.is_relative_to((H/'candidate-root').resolve()):h20sources[p.relative_to(H/'candidate-root').as_posix()]=verify(ref)
assert set(h20sources)==expected_h20
test=Path(h20sources['internal/domain/backup_history20_upgrade_test.go']['path']).read_text(encoding='utf-8')
parents=sorted(re.findall(r'^func (TestHistory20[A-Za-z0-9_]+)\(',test,re.M))
assert len(parents)==5
cases=re.search(r'for _, tc := range \[\]string\{([^}]+)\}',test).group(1)
subcases=re.findall(r'"([^"]+)"',cases)
assert subcases==['migration-hash','extra-numbered-migration','foreign-table','session-addon']
terminals=sorted(parents+['TestHistory20RejectsReleaseAndSourceDrift/'+x for x in subcases])
assert len(terminals)==9
sources.update(h20sources);preserved.update(parents)
declared=set()
for rel,ref in sources.items():
 if rel.endswith('_test.go'):declared.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',Path(ref['path']).read_text(encoding='utf-8'),re.M))
assert all(sources[k]==v for k,v in old_sources.items() if k not in h20sources)
assert sources['internal/domain/client_protocol_attach_contract_windows_test.go']==old_sources['internal/domain/client_protocol_attach_contract_windows_test.go']
choice['schema']='researchos.root-history20-five-parent-integration-choice.v1'
choice['source_components'].append({'component':'H20R1','candidate_namespace':H.relative_to(B).as_posix(),'source_handoff':hp,'source_manifest':hm,'independent_handoff':vp,'independent_manifest':vm})
choice['base_driver_refs'] += [use(p) for p in [prep,val,BASE/'HDF.json',BASE/'MF.json',BASE/'source.integration.choice.json',ACT/'validation.closed.json']]
choice['base_driver_refs'].append(actual_overlay_ref)
choice.update(expected_source_count=len(sources),exact_parent_names=parents,expected_terminal_names=terminals,expected_terminal_count=len(terminals),source_preserved_parent_names=sorted(preserved),source_preserved_parent_count=len(preserved),source_preserved_nonselected_parent_count=len(preserved-set(parents)),all_source_file_declared_parent_names=sorted(declared),ordinary_history20_full_release_program_rehearsal_authority='OPEN_NOT_EXECUTED',history20_scope='PUBLIC_FIXTURE_A20_TO_PLAIN21_ONLY',actual_T11_overlay_ref=actual_overlay_ref,actual_T11_closed_ref=use(ACT/'validation.closed.json'),actual_T11_sources_preserved_except_exact_H20_paths=True,h20_candidate_paths=sorted(h20sources),fresh_worktree=str(T),fresh_isolation_output=str(ISO),fresh_validation_output=str(OUT),fresh_environment=str(ENV))
put('source.integration.choice.json',choice)
(N/'base').mkdir(exist_ok=True)
diffs=[]
for origin,name,isprep in [(prep,'prepare_history20_five_parent.actual_owned.py',True),(val,'validate_history20_five_parent.actual_owned.py',False)]:
 raw=origin.read_bytes();s=raw.decode('utf-8');newline='\r\n' if '\r\n' in s else '\n';s=s.replace('\r\n','\n')
 replacements=[
 ('D:/作品集/ResearchOS/research-os/.local/worktrees/t11s-1791516205000',T.as_posix()),
 ('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/attach-fixture-two-parent-sparse-isolation-root-1791516205000',ISO.as_posix())]
 if isprep:
  replacements += [('attach-fixture-current-two-parent-isolation-toolenv-','history20-five-parent-isolation-toolenv-')]
 else:
  replacements += [
   ('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/integration_codex/attach-fixture-two-parent-sparse-target-root-1791516205000',OUT.as_posix()),
   ('researchos.root-attach-fixture-current-two-parent-integration-choice.v1','researchos.root-history20-five-parent-integration-choice.v1'),
   ('D:/作品集/ResearchOS/research-os/.local/attach-fixture-current-two-parent-run-env-t11-1a11e7f5205729390aaee9f47b28ce6',ENV.as_posix()),
   ('assert len(sources)==58 and choice["expected_source_count"]==58',f'assert len(sources)=={len(sources)} and choice["expected_source_count"]=={len(sources)}'),
   ("assert new_tests=={'TestClientAttachSettledAcquisitionCompletesAndReplays', 'TestClientAttachPreservesStaleAndBindingGates'}",'assert new_tests=='+repr(set(parents))),
   ('relative.startswith("internal/domain/") and (relative.endswith(".go") or relative.startswith("internal/domain/testdata/"))','(relative.startswith("internal/domain/") and (relative.endswith(".go") or relative.startswith("internal/domain/testdata/"))) or (item["component"]=="H20R1" and relative=="ops/backup/main.go")'),
   ('attach-fixture-current-two-parent.test.exe','history20-five-parent.test.exe'),
   ('attach-fixture-current-two-parent-jsonl','history20-five-parent-jsonl'),
   ('ordinary_history20_full_release_program_rehearsal_authority="BLOCKED"','ordinary_history20_full_release_program_rehearsal_authority="OPEN_NOT_EXECUTED",history20_scope="PUBLIC_FIXTURE_A20_TO_PLAIN21_ONLY",expected_terminal_names=choice["expected_terminal_names"],legacyB_release_program_ProductOwner_flow="OPEN_NOT_EXECUTED"'),
   ('starts==set(actions) and new_tests.issubset(starts)','starts==set(actions)==set(choice["expected_terminal_names"]) and new_tests.issubset(starts) and len(actions)==9'),
   ('ATTACH_FIXTURE_TWO_PARENT_TARGET_SCOPE_PASSED_COMPONENT_ONLY_FULL_SCOPE_BLOCKED','HISTORY20_FIVE_PARENT_A20_TO21_SCOPE_PASSED_FULL20_TO24_OPEN'),
   ('FAILED_ATTACH_FIXTURE_TWO_PARENT_COMPILE_OR_TARGET_EXECUTION_CLOSED','FAILED_HISTORY20_FIVE_PARENT_COMPILE_OR_TARGET_EXECUTION_CLOSED')]
  needle=' candidate=(B/item["candidate_namespace"]/"candidate-root").resolve()\n'
  added=needle+' if item["component"]=="H20R1":\n  actual_T11=json.loads(Path(choice["actual_T11_overlay_ref"]["path"]).read_bytes())\n  assert sources=={key:verify(ref) for key,ref in actual_T11["sources"].items()} and len(sources)==58\n  assert {Path(ref["path"]).resolve().relative_to(candidate).as_posix() for ref in members(item["source_manifest"]) if Path(ref["path"]).resolve().is_relative_to(candidate)}==set(choice["h20_candidate_paths"])\n'
  replacements.append((needle,added))
 for oldtxt,newtxt in replacements:
  count=s.count(oldtxt);assert count>=1,(name,oldtxt)
  s=s.replace(oldtxt,newtxt)
 ast.parse(s)
 inverse=s
 for oldtxt,newtxt in reversed(replacements):assert newtxt in inverse;inverse=inverse.replace(newtxt,oldtxt)
 assert inverse.replace('\n',newline).encode()==raw,name
 (N/'base'/origin.name).write_bytes(raw)
 p=N/name;p.write_bytes(s.replace('\n',newline).encode('utf-8'))
 diffs.append({'original':use(origin),'candidate':pin(p),'exact_byte_inverse':True,'replacements':replacements})
for ref in list(inputs.values()):assert pin(ref['path'])==ref
put('input-pins.json',list(inputs.values()))
put('source-replacements.json',diffs)
put('composition.json',{'base_actual_T11_source_count':len(old_sources),'final_source_count':len(sources),'h20_paths':{k:{'prior_overlay_ref':old_sources.get(k),'replacement_ref':v,'existed_in_repository':(R/k).is_file()} for k,v in h20sources.items()},'non_h20_T11_sources_exactly_preserved':True,'AF_source_exactly_preserved':True,'final_sources':sources,'previous_preserved_parent_count':len(old_preserved),'preserved_parent_count':len(preserved),'all_declared_parent_count':len(declared),'selected_parent_names':parents,'expected_terminal_names':terminals,'actual_execution':False})
print(json.dumps({'source_only':True,'source_count':len(sources),'previous58_count':len(old_sources),'preserved_parent_count':len(preserved),'declared_parent_count':len(declared),'five_parents':parents,'nine_expected_terminals':terminals,'h20_overlay_preexisting_count':sum(k in old_sources for k in h20sources),'input_count':len(inputs)}))
