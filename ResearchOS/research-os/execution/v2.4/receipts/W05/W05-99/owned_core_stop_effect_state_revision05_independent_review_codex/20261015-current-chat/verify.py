import pathlib, json, hashlib, subprocess, sys, shutil
E=pathlib.Path(r'D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/owned_core_stop_effect_state_revision05_independent_review_codex/20261015-current-chat');R=pathlib.Path('D:/作品集/ResearchOS/research-os')
S=R/'execution/v2.4/receipts/W05/W05-99/resume_cp398_codex/20261015-current-chat/continuation-cp522/owned-core-stop-effect-state-r5-independent-review-scope.json'
s=json.loads(S.read_text(encoding='utf-8-sig'));W=pathlib.Path(s['worktree']);T=pathlib.Path(s['own_temporary_root']);C=pathlib.Path(s['approved_c_image_fixture_root'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
def cap(args):
    r=subprocess.run([sys.executable,'-B','-X','utf8',str(E/'reviewer_logger.py'),*args],cwd=W,capture_output=True)
    assert r.returncode==0,(args,r.returncode,r.stderr.decode('utf-8'))
    return r.stdout
checks=[]
for i in s['inputs']:
    p=R/i['path'];actual=pin(p);assert actual['sha256']==i['sha256'],str(p);checks.append(actual)
assert sha(S)=='34741e24b390fdeb8ed54e59ec6f3b0402383ed80561ba14ec94bc3dcf8bc315'
assert cap(['git','rev-parse','HEAD']).decode().strip()==s['source_commit']
assert cap(['git','rev-parse','HEAD^{tree}']).decode().strip()==s['source_tree']
status=cap(['git','status','--porcelain=v1','--untracked-files=all']);assert not status,status
changes=cap(['git','diff','--name-only','ab308912117dac59cadd5aa2e75b46a418e41b6b',s['source_commit']]).decode().splitlines();assert sorted(changes)==sorted(s['delta_paths_readonly'])
full=cap(['git','diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1',s['source_commit']]).decode().splitlines();assert sorted(full)==sorted(s['source_allowlist_readonly'])
for label,base,paths in [('delta2','ab308912117dac59cadd5aa2e75b46a418e41b6b',changes),('whole19','4f4023c956f84d65743f39ce77d6c8899a21ada1',full)]:
    (E/(label+'.patch')).write_bytes(cap(['git','diff','--binary','--full-index',base,s['source_commit'],'--',*paths]))
prior=R/'execution/v2.4/receipts/W05/W05-99/owned_core_stop_authority_revision04_independent_review_codex/20261015-current-chat/review.json'
p=json.loads(prior.read_text(encoding='utf-8'));old={x['path']:x for x in p['full19']}
files=[]
for name in full:
    rec=pin(W/name);rec['relative_path']=name;rec['unchanged_from_r4']=rec['sha256']==old[name]['sha256'];files.append(rec)
assert sum(x['unchanged_from_r4'] for x in files)==17
archives=[]
for case in sorted(E.glob('fixture-e2e-*')):
    result=json.loads((case/'case-result.json').read_text(encoding='utf-8'))
    src=T/case.name/'operation';dest=case/'operation-archive';shutil.copytree(src,dest)
    for item in dest.rglob('*'):
        if item.is_file():archives.append(pin(item))
    result['operation_archive']=str(dest)
    if result['mode']=='positive':
        plan=json.loads((dest/'plan.json').read_text());post=json.loads((dest/'POSTFLIGHT.json').read_text());exitrec=json.loads((dest/'NATIVE_EXIT.json').read_text())
        assert post==result['result'];assert post['postflight']==plan['baseline'];assert plan['baseline']['tables']==87 and plan['baseline']['rows']==35
        assert exitrec['native']==post['native'] and post['native']==dict(terminate_calls=1,exit_observed=True,exit_code=1381191507,before_signal=False)
        for label in ['cli-real-stop-once','cli-real-inspect','cli-repeat-commit-readonly']:
            assert json.loads((case/(label+'.stdout.bin')).read_bytes())==post
    else:
        assert result['native_signal_count']==0 and not result['stop_grant_built']
        assert not (case/'STOP-grant.json').exists()
        assert not (src/'STOP_ATTEMPT.json').exists() and not (src/'TERMINATE_INTENT.json').exists()
        assert result['baseline']['tables']==87 and result['baseline']['rows']==36
    assert json.loads((case/'core-after.json').read_text())['native_exit']==0
assert len(list(C.iterdir()))==2 and all(x.suffix=='.exe' for x in C.iterdir())
record=dict(scope=pin(S),source_commit=s['source_commit'],source_tree=s['source_tree'],source_clean=True,input_pins=checks,source_files=files,delta2=pin(E/'delta2.patch'),whole19=pin(E/'whole19.patch'),operation_archives=archives,c_files=[pin(x) for x in C.iterdir()],actual_authority=False,formal_increment=0)
(E/'source-fixture-verification.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(source_clean=True,full19=len(files),unchanged17=17,delta2=len(changes),cases=3,c_files_only_exe=True),indent=2))
