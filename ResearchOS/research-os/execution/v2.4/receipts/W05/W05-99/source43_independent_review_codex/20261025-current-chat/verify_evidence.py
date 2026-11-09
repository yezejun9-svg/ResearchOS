import pathlib,json,hashlib,sys
sys.stdout.reconfigure(encoding='utf-8')
out=pathlib.Path(__file__).parent
repo=pathlib.Path('D:/作品集/ResearchOS/research-os')
author=out.parent.parent/'source43_b_stop_finalpath_codex'/'20261025-current-chat'
scopepath=repo/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp529/source43-resume-scope.json'
raw=scopepath.read_bytes();assert hashlib.sha256(raw).hexdigest()=='ba67fadc116d087735c122602118322c349cf35e288a44a570569eae7aec731a'
refs=[]
def check(node):
    if isinstance(node,dict):
        if all(k in node for k in ('path','sha256','bytes')):
            p=pathlib.Path(node['path']);p=p if p.is_absolute() else repo/p
            data=p.read_bytes();assert len(data)==node['bytes'] and hashlib.sha256(data).hexdigest()==node['sha256'],str(p)
            refs.append({'path':str(p),'sha256':node['sha256'],'bytes':node['bytes']})
        for v in node.values():check(v)
    elif isinstance(node,list):
        for v in node:check(v)
check(json.loads(raw))
for cmd,name in [('042-full43-diff','full43-from-Main4f.patch'),('043-fix2-diff','fix2-from-baseB.patch')]:
    assert (out/'commands'/cmd/'stdout.raw').read_bytes()==(author/name).read_bytes(),name
matrix=json.loads((author/'claim-test-matrix.json').read_text(encoding='utf-8'))
summaries=[]
for row in matrix['results']:
    log=author/row['receipt']/'stdout.raw'
    events=[]
    for line in log.read_text(encoding='utf-8').splitlines():
        try:events.append(json.loads(line))
        except json.JSONDecodeError:pass
    parsed={state:[e['Test'] for e in events if isinstance(e,dict) and e.get('Action')==state and e.get('Test')] for state in ['pass','fail','skip']}
    if events:
        for state in parsed:assert parsed[state]==row[state+'_events'],(row['receipt'],state)
    summaries.append({'receipt':row['receipt'],'native_exit':row['native_exit'],'events_parsed':bool(events),'counts':{k:len(v) for k,v in parsed.items()}})
own=[]
for label in ['023-roots-native','028-b-closure-replay','033-compiled-stop-positive-refusal','034-compiled-stop-postflight-refusal','041-b-commit-failure']:
    p=out/'commands'/label
    assert json.loads((p/'result.json').read_text())['native_exit']==0
    text=(p/'stdout.raw').read_text(encoding='utf-8')
    if text.startswith('{'):
        events=[json.loads(line) for line in text.splitlines()]
        passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')]
        skipped=[e['Test'] for e in events if e.get('Action')=='skip' and e.get('Test')]
        failed=[e['Test'] for e in events if e.get('Action')=='fail' and e.get('Test')]
    else:
        passed=[line.split(': ',1)[1].split(' (')[0] for line in text.splitlines() if line.startswith('--- PASS: ')]
        skipped=[line for line in text.splitlines() if '--- SKIP:' in line]
        failed=[line for line in text.splitlines() if '--- FAIL:' in line]
    assert passed and not skipped and not failed
    own.append({'command':label,'pass_events':passed,'skip_events':skipped,'fail_events':failed,'native_exit':0})
info=(out/'commands/035-buildinfo/stdout.raw').read_text(encoding='utf-8')
assert info.count('vcs.revision=085b4711afe0c1288448b174eef24ecd5af0551b')==3 and info.count('vcs.modified=false')==3
assert (out/'commands/038-final-clean/stdout.raw').read_bytes()==b''
assert (out/'commands/036-compiled-cli-refusal/stderr.raw').read_text().strip()=='STOP_GRANT_UNCONFIGURED'
scope=json.loads((repo/'execution/v2.4/receipts/W05/W05-99/resume_cp528_codex/20261025-current-chat/continuation-cp531/Source43-independent-review-scope.json').read_text(encoding='utf-8'))
names=(out/'commands/014-composition-diff/stdout.raw').read_text().splitlines();assert sorted(names)==sorted(scope['source_allowlist'])
result={'inherited_references':refs,'author_test_matrix_recomputed':summaries,'own_test_results':own,'full43_and_fix2_patches_exact':True,'buildinfo_three_exact_clean':True,'source_names_exact43':True,'compiled_cli_refusal':{'native_exit':1,'reason':'STOP_GRANT_UNCONFIGURED','expected':True},'CI':{'external_ci_run':None,'kind':'local Windows native executions','no_remote_CI_claim':True}}
(out/'evidence-verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'inherited_refs_verified':len(refs),'author_matrix':summaries,'own_results':own,'patches':'byte-equal','buildinfo':'three exact clean'},ensure_ascii=False,indent=2))
