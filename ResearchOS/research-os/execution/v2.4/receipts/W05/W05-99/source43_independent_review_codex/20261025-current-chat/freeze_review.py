import pathlib,json,hashlib,datetime,sys
sys.stdout.reconfigure(encoding='utf-8')
base=pathlib.Path(__file__).parent
def pin(p):
    raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,data):
    target=base/name
    assert not target.exists(),name
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
commands=[]
for folder in sorted((base/'commands').iterdir()):
    recipe=json.loads((folder/'recipe.json').read_text(encoding='utf-8'))
    result=folder/'result.json'
    commands.append({'id':folder.name,'recipe':pin(folder/'recipe.json'),'argv':recipe['argv'],'cwd':recipe['cwd'],'env_overrides':recipe['env_overrides'],'native_exit':json.loads(result.read_text(encoding='utf-8'))['native_exit'] if result.exists() else None,'capture_state':'CLOSED' if result.exists() else 'FINALIZER_RUNNING_SEALED_SEPARATELY','files':[pin(p) for p in sorted(folder.iterdir()) if p.is_file() and not (folder.name=='047-freeze' and p.name in ['stdout.raw','stderr.raw'])]})
save('command-index.json',{'schema':'researchos.source43-independent-command-index.v1','commands':commands,'self_result_boundary':'047 result and streams will be bound by FINAL-seal.json; no recursive self hashing'})
diagnostics=[
 {'id':'BOOTSTRAP-000','class':'CAPTURE_EXCEPTION','native_exit':0,'operation':'Read canonical AGENTS, Get-FileHash SHA256 scope, read scope','tool_chunk':'66d013','prewritten_recipe':False,'separate_raw_streams':False,'note':'Read-only bootstrap before runner creation. Tool transcript retained in current chat; not represented as native per-command capture.'},
 {'id':'LAUNCHER-002','class':'LAUNCHER_FAILURE_BEFORE_RECIPE','native_exit':1,'tool_chunk':'eefd8a','attempted':'002-read','cause':'Reviewer inspect.py shadowed Python stdlib inspect while argparse imported dataclasses. FileNotFoundError on --label before subprocess execution.','prewritten_recipe':False,'separate_raw_streams':False,'resolution':'Renamed reviewer-only script to read_sources.py; executed 004-read.'},
 {'id':'LAUNCHER-003','class':'LAUNCHER_FAILURE_BEFORE_RECIPE','native_exit':1,'tool_chunk':'c32ca9','attempted':'003-worktree-add','cause':'Same reviewer Python stdlib shadowing; Git subprocess was never invoked.','prewritten_recipe':False,'separate_raw_streams':False,'resolution':'005 is first actual worktree add; no source changed by failed launcher.'},
 {'id':'020-roots-native','class':'BUILD_SETUP_FAILURE','native_exit':1,'cause':'Sparse checkout lacked evaluation packages; no tests ran.','resolution':'021 adds immutable evaluation/spec/test/support dirs; 023 then passes.'},
 {'id':'036-compiled-cli-refusal','class':'EXPECTED_REFUSAL','native_exit':1,'cause':'STOP_GRANT_UNCONFIGURED','count_as_unexpected_failure':False},
 {'id':'044-evidence-check','class':'REVIEW_SCRIPT_FAILURE','native_exit':1,'cause':'Default Windows text decoder misread UTF-8 scope JSON.','resolution':'Reviewer script explicitly uses UTF-8; 045 verifies all references. Candidate untouched.'}
]
save('diagnostic-ledger.json',{'schema':'researchos.source43-independent-diagnostics.v1','entries':diagnostics,'counts':{'pre_recipe_bootstrap_exceptions':1,'pre_recipe_launcher_failures':2,'recorded_unexpected_native_nonzero':2,'expected_native_refusals':1,'candidate_test_failures':0},'author_and_historical_ledgers':'Referenced without reset or rewrite; author-verification.json and inherited references bind their immutable evidence.','definition':'Command-native nonzero, launcher failure, expected refusal and test event counts are separate; no reassignment to author source failures.'})
evidence=json.loads((base/'evidence-verification.json').read_text(encoding='utf-8'))
save('claim-test-matrix.json',{'schema':'researchos.source43-independent-claims.v1','source_contract':'REVIEW.md','results':evidence['own_test_results'],'top_level_pass':11,'subtest_pass':1,'skip':0,'failed_test_events':0,'expected_cli_refusal':evidence['compiled_cli_refusal'],'CI':evidence['CI'],'inherited_author_matrix':evidence['author_test_matrix_recomputed']})
pins=json.loads((base/'pins-verification.json').read_text(encoding='utf-8'))
wt=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/source43-independent-review-20261025')
for entry in pins['files']:
    actual=pin(wt/entry['path']);assert actual['sha256']==entry['sha256'] and actual['bytes']==entry['bytes']
review={'schema':'researchos.source43-independent-review.v1','verdict':'LIMITED_SOURCE_ACCEPTED','reviewer':'codex:/root/source43_independent_review_20261025','model':'gpt-6-astra','reasoning_effort':'high','candidate':'085b4711afe0c1288448b174eef24ecd5af0551b','tree':'227d36324fd1053c285d0b2846a2b707ac2df6bd','findings':[],'blocking_findings':[],'source_edits':False,'source_pins':'pins-verification.json','independent_substantive_review':'REVIEW.md','claim_matrix':'claim-test-matrix.json','diagnostics':'diagnostic-ledger.json','root_adoption':False,'main_import':False,'actual':False,'formal_increment':0,'C57_issued':False,'limitations':['Controlled Windows fixture and static source evidence only','No complete grant-bound CLI positive, production data repair, live provider or formal acceptance','Inherited exact15s/foreignSID/hostile-race/cleanup-cartesian/CloseHandle injection limitations remain','Existing truncated registry is not rewritten','Explicit pre-recipe bootstrap and two launcher capture exceptions retained','Future C must independently prove closure Check then actual transaction completion then Close']}
save('review.json',review)
binarybase=pathlib.Path('C:/Users/yqyyds/.codex/researchos-fixture-cache/source43-independent-review-20261025/bin')
author=base.parent.parent/'source43_b_stop_finalpath_codex'/'20261025-current-chat'
manifest={'schema':'researchos.source43-independent-final.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'FROZEN_LIMITED_SOURCE_ACCEPTED','candidate':review['candidate'],'tree':review['tree'],'report':pin(base/'REVIEW.md'),'review':pin(base/'review.json'),'author_final_and_supplement':[pin(author/name) for name in ['FINAL-manifest.json','FINAL-supplement.json','FINAL-supplement-seal.json']],'retained_rebuildable_binaries':[pin(p) for p in sorted(binarybase.glob('*.exe'))],'files':[],'seal':'FINAL-seal.json','self_result_boundary':'047-freeze stdout/stderr/result and FINAL itself are closed by FINAL-seal; seal runner closure is not recursively indexed','authority':{'root_adoption':False,'actual':False,'formal_increment':0}}
for p in sorted(base.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts:continue
    rel=p.relative_to(base).as_posix()
    if rel.startswith('commands/047-freeze/') and p.name in ['stdout.raw','stderr.raw','result.json']:continue
    manifest['files'].append(pin(p))
save('FINAL-manifest.json',manifest)
print(json.dumps({'manifest':pin(base/'FINAL-manifest.json'),'review':pin(base/'review.json'),'report':pin(base/'REVIEW.md'),'verdict':review['verdict'],'closed_commands':sum(c['capture_state']=='CLOSED' for c in commands),'current_finalizer':'047-freeze'},ensure_ascii=False,indent=2))
