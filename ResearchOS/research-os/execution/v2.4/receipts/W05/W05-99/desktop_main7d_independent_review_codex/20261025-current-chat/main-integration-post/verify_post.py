import hashlib,json,pathlib,subprocess
E=pathlib.Path(__file__).parent;I=E/'inputs';R=pathlib.Path('D:/作品集/ResearchOS/research-os');PRE=E.parent/'main-integration-preflight'
C='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419';T='1d44a02c9483fc529b08ffe81895ec443920bdd1';BASE='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e';C57='03aa4d687dfaa541d9b18d4c766805307a537d1d'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(name):return json.loads((I/name).read_bytes())
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
put('002-verify.recipe.json',{'mode':'READ_ONLY_ACTUAL_GIT_HEAD_INDEX_SEVEN_FILES_AND_CAPTURED_PRESERVATION','root':str(R),'no_tests_builds_native_or_original_data_access':True})
commands=[]
def git(root,*args,allowed=(0,)):
    argv=['git','--no-optional-locks','-C',str(root),*args]
    p=subprocess.run(argv,capture_output=True)
    commands.append({'argv':argv,'native_exit':p.returncode,'stdout_sha256':hashlib.sha256(p.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(p.stderr).hexdigest(),'expected_exit_codes':list(allowed)})
    assert p.returncode in allowed,(argv,p.returncode,p.stderr)
    return p.stdout,p.returncode
def textgit(*args):return git(R,*args)[0].decode().strip()
captured=json.loads((E/'CAPTURED-INPUTS.json').read_bytes());refs={str(pathlib.Path(r['path'])):r for r in captured}
for row in captured:assert sha(row['path'])==sha(row['copy'])==row['sha256'] and pathlib.Path(row['path']).stat().st_size==row['bytes']
def ref_check(row):
    p=pathlib.Path(row['path']);r=refs[str(p)]
    assert row['sha256']==r['sha256'] and row['bytes']==r['bytes']
scope=read('Desktop-Main-integration-scope.json')
assert scope['operation']=='LOCAL_FAST_FORWARD_ONLY' and scope['base']==BASE and scope['candidate']==C and scope['tree']==T
for row in scope['bound_evidence']+[scope['runner_ref'],scope['post_gate_ref']]:
    assert sha(row['path'])==row['sha256'] and pathlib.Path(row['path']).stat().st_size==row['bytes']
outer=read('090-desktop-main-integration.recipe.result.json');result=read('result.json');gr=read('git-result.json');gc=read('git-command.json')
assert outer['native_exit']==gr['native_exit']==result['git_native_exit']==0
for row in [outer['recipe'],outer['stdout'],outer['stderr'],gr['stdout'],gr['stderr'],result['scope_ref'],result['before_ref'],result['after_ref']]:ref_check(row)
assert gc['argv']==['git','-c','maintenance.auto=false','-c','gc.auto=0','merge','--ff-only','--no-edit',C]
assert pathlib.Path(gc['cwd'])==R and b'Fast-forward' in (I/'git.stdout.raw').read_bytes() and not (I/'git.stderr.raw').read_bytes()
assert result['Main']==C and result['tree']==T and result['previous_Main']==BASE
assert result['original_data_action'] is False and result['C57_merge'] is False and result['source_or_native_retest'] is False and result['formal_increment']==0
assert textgit('rev-parse','HEAD')==C and textgit('rev-parse','HEAD^{tree}')==T and textgit('rev-parse','HEAD^')==BASE
assert textgit('branch','--show-current')=='main' and not textgit('diff','--cached','--name-only')
delta=textgit('diff-tree','--no-commit-id','--name-status','-r',C).splitlines()
assert len(delta)==7 and sorted(x.split('\t')[1] for x in delta)==scope['allowed_paths']
assert sum(x.startswith('A\t') for x in delta)==6 and sum(x.startswith('M\t') for x in delta)==1
pre=json.loads((PRE/'MAIN-SEVEN-PATHS-INDEPENDENT.json').read_bytes())
dirty=git(R,'status','--porcelain=v1','--untracked-files=no')[0].decode().splitlines()
assert dirty==pre['tracked_dirty_paths'] and len(dirty)==20
seven=[]
for row in pre['seven_paths']:
    p=R/row['path'];blob=git(R,'show','HEAD:'+row['path'])[0]
    assert sha(p)==hashlib.sha256(blob).hexdigest()==row['candidate_sha256'] and p.stat().st_size==row['candidate_bytes']
    seven.append({'path':row['path'],'sha256':sha(p),'bytes':p.stat().st_size,'disk_equals_reviewed_blob':True})
before=read('preservation.before.json');after=read('preservation.after.json')
assert before['Main']==BASE and after['Main']==C and after['Main_tree']==T and after['Main_previous']==BASE
for k in ['C57_frozen','dirty_path_count','protected','old_assets','new_assets']:assert before[k]==after[k]
assert before['C57_frozen']==C57 and before['dirty_path_count']==20 and before['protected']==9 and before['old_assets']==33 and before['new_assets']==3
before_refs=before['verified_refs'];after_refs=after['verified_refs']
assert len(before_refs)==48 and len(after_refs)==55 and after_refs[:48]==before_refs
assert {r['path']:r['sha256'] for r in after_refs[48:]}=={str(R/r['path']):r['sha256'] for r in seven}
assert after['integrated_exact_paths']==scope['allowed_paths']
Cpath=R/'.local/worktrees/qualification-maintenance-c57-20261025'
assert git(Cpath,'rev-parse','HEAD')[0].decode().strip()==C57 and not git(Cpath,'status','--porcelain=v1','--untracked-files=all')[0]
ancestor=git(R,'merge-base','--is-ancestor',C57,C,allowed=(0,1))[1]
assert ancestor==1,'Unexpected C57 ancestor; investigate before acceptance'
oldrefs=json.loads((PRE/'INPUT-REFS.json').read_bytes())
command_refs=[]
for rel in ['execution/commands.json','execution/v2.4/commands.json','execution/command_dispatcher/dispatch.py','apps/desktop/package.json','tests/ui/check/main.py']:
    prior=next(r for r in oldrefs if r.get('path')==rel)
    assert sha(R/rel)==prior['sha256'];command_refs.append({'path':rel,'sha256':sha(R/rel),'unchanged_from_preflight':True})
registry=json.loads((R/'execution/v2.4/commands.json').read_bytes())['commands']
assert registry['desktop.shell_launch']['state']==registry['desktop.installer_build']['state']=='UNBOUND'
checkpoint=json.loads((R/'execution/v2.4/checkpoint.json').read_bytes());owner=json.loads((R/'execution/v2.4/path_ownership.json').read_bytes())
assert checkpoint['revision']==555 and owner['revision']==341 and len(checkpoint['failure_counters'])==2250
put('ACTUAL-READ-ONLY-GIT-COMMANDS.json',commands)
summary={'verdict':'EXACT_MAIN_FAST_FORWARD_POST_REVIEW_PASS','main_head':C,'main_tree':T,'direct_parent':BASE,'branch':'main','index_empty':True,'exact_delta':delta,'seven_files':seven,'original_20_tracked_dirty_preserved':True,'captured_original_48_refs_identical_before_after':True,'after_refs_count':55,'C57_head':C57,'C57_clean':True,'C57_not_ancestor_of_Main':True,'registry_refs':command_refs,'desktop_platform_commands':'UNBOUND_UNCHANGED','checkpoint_revision':555,'ownership_revision':341,'mixed_diagnostic_history_count':2250,'root_merge_native_exit':0,'outer_native_exit':0,'unexpected_review_diagnostics':0,'expected_negative_git_ancestry_exit':1,'tests_builds_native_rerun':0,'source_or_shared_state_writes':0,'original_data_actions':0,'formal_increment':0,'installer_or_C57_acceptance':False}
put('POST-INTEGRATION-INDEPENDENT-CHECK.json',summary)
print(json.dumps({k:v for k,v in summary.items() if k not in ['seven_files','registry_refs','exact_delta']},ensure_ascii=False))
