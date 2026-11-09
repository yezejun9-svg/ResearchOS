"""Independently check saved R05/R08/R09 evidence without test execution."""
from pathlib import Path
import json, hashlib, re, datetime

out=Path(__file__).resolve().parent
root=out.parents[4]
base=root/'execution/receipts/W21/current-domain-delta/27ced22'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
report=read(base/'report.json');before=read(base/'before.json')
assert report['source_manifest']==before['source_manifest']
assert report['source_drift']==[] and report['formal_acceptance'] is False
for p,h in report['source_manifest'].items():assert sha(root/p)==h,p
hashes={p.relative_to(root).as_posix():sha(p) for p in base.rglob('*') if p.is_file()}
reviews={}
all_refs=[]
for group,want_tests,want_assertions in [('R05',11,18),('R08',9,54),('R09',2,19)]:
    g=report['groups'][group]
    raw=base/group/'stdout.jsonl'
    assert sha(raw)==g['stdout_sha256']
    assert sha(base/group/'stderr.log')==g['stderr_sha256']
    argv=g['argv'];selector=argv[argv.index('-run')+1]
    assert selector.startswith('^(') and selector.endswith(')$')
    names=selector[2:-2].split('|');assert len(names)==want_tests
    events=[json.loads(line) for line in raw.read_text(encoding='utf-8').splitlines()]
    runs=[e['Test'] for e in events if e.get('Action')=='run' and '/' not in e.get('Test','')]
    passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test') and '/' not in e['Test']]
    assert sorted(names)==sorted(runs)==sorted(passed)==sorted(g['passed_tests'])
    assert not [e for e in events if e.get('Action') in ['fail','skip']]
    packages=[e for e in events if e.get('Action')=='pass' and not e.get('Test')]
    assert len(packages)==1
    buffers={};starts={};found=[]
    for line,e in enumerate(events,1):
        if e.get('Action')!='output':continue
        key=(e.get('Package'),e.get('Test'))
        if not buffers.get(key):starts[key]=line
        buffers[key]=buffers.get(key,'')+e.get('Output','')
        while '\n' in buffers[key]:
            text,buffers[key]=buffers[key].split('\n',1)
            m=re.search(r'\b\w+_ASSERTION\s+(\{.*\})',text)
            if m:
                a=json.loads(m.group(1));assert a['status']=='PASS'
                found.append(a)
                all_refs.append({'group':group,'test':key[1],'assertion_id':a['assertion_id'],
                    'raw':raw.relative_to(root).as_posix(),'raw_line':starts[key],'raw_end_line':line})
            starts[key]=line
    assert not any(v.strip() for v in buffers.values())
    assert len(found)==want_assertions and len({a['assertion_id'] for a in found})==want_assertions
    assert sorted(found,key=lambda x:x['assertion_id'])==sorted(g['assertions'],key=lambda x:x['assertion_id'])
    if group=='R05':
        assert g['exit_code'] is None
        assert g['exit_code_capture']=='NOT_PERSISTED_BEFORE_INITIAL_PARSER_EXCEPTION'
        assert g['original_python_wrapper_exit_code']==1 and g['test_execution_repeated'] is False
        assert not (base/group/'command.json').exists()
        assert (base/'initial-parser-error.txt').stat().st_size>0
        exit_evidence='UNKNOWN_NOT_CAPTURED; wrapper exit 1; raw package PASS is not process exit 0'
    else:
        command=read(base/group/'command.json')
        assert command['exit_code']==g['exit_code']==0 and command['argv']==argv and command['cwd']==g['cwd']
        exit_evidence='Actual Go exit 0 persisted in command.json'
    reviews[group]={'verdict':'PASS_SAVED_TARGETED_EVIDENCE_WITH_LIMITS','tests':want_tests,
        'assertions':want_assertions,'skips':0,'raw_package_status':'PASS','go_exit_code':g['exit_code'],
        'exit_evidence':exit_evidence,'raw_sha256':sha(raw),'selector':selector,'test_execution_by_reviewer':False}
result={'schema':'W21_ROOT_BATCHES_INDEPENDENT_EVIDENCE_REVIEW_V1','reviewer':'codex:/root/control_drain',
    'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'verdict':'PASS_TARGETED_EVIDENCE_WITH_R05_PROCESS_EXIT_UNKNOWN',
    'source_revision':report['execution_head'],'source_files_hash_verified':len(report['source_manifest']),
    'source_drift':[],'groups':reviews,'assertion_refs':all_refs,'artifact_hashes':hashes,
    'formal_case_acceptance':False,'canonical_acceptance_changed':False,
    'scope':'Read-only saved evidence review of public synthetic SQLite/HTTP and actual Windows storage.',
    'limits':['R05 process exit was not persisted. The wrapper exited 1; package PASS is preserved without inventing exit 0.',
        'No tests were rerun by this reviewer; no provider/native child/private protected evaluation/production activation.',
        'R05 does not newly accept all C11-C16; R08 does not newly accept full A02/A03; R09 does not newly accept full A12.',
        'R09 restores generic historical fixture data, not current-control authorization or production recovery activation.',
        'Verified manifests are bounded inventories, not a proven transitive dependency closure.']}
(out/'root-batches-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(out/'root-batches-review.md').write_text('''# W21 R05 / R08 / R09 独立证据核查

结论：现有定向测试证据通过；R05 的 Go 进程退出码仍未知。没有重跑测试，没有改变正式 case 验收状态。

| 批次 | 实际测试 | 完整断言 | Go 进程退出码 | 原始包结果 |
|---|---:|---:|---|---|
| R05 | 11 | 18 | 未保存；Python wrapper 实际退出 1 | PASS |
| R08 | 9 | 54 | command.json 已保存 0 | PASS |
| R09 | 2 | 19 | command.json 已保存 0 | PASS |

独立按 Package/Test 拼接 Go Output 后解析完整行，逐条比对 report.json 的所有 assertion 对象；验证非空精确 selector、每个 run/pass、无 fail/skip、原始 stdout/stderr 哈希、before/report/current 源清单一致。逐断言原始行号与完整文件哈希见 root-batches-review.json。

R05 的初始解析错误与原始日志均保留，未把 package PASS 当作实际进程退出 0。其限制来自命令回执缺失，不能通过本次只读审查补造。

范围仅限 public synthetic SQLite/HTTP 与真实 Windows 存储。R09 是通用旧夹具数据恢复，不是 current-control 授权。未签发完整 C11–C16、A02/A03、A12、新 native child、provider、私有评测或生产激活验收；源清单也不是已证明的传递依赖闭包。
''',encoding='utf-8')
print(json.dumps({'verdict':result['verdict'],'groups':{k:{'tests':v['tests'],'assertions':v['assertions'],'exit':v['go_exit_code']} for k,v in reviews.items()},'source_files':len(report['source_manifest'])}))

# BEGIN POST-RUN DEPENDENCY SUPPLEMENT: independently executable, no tests.
import subprocess
supplement_path=base/'dependency-supplement.json'
supplement=read(supplement_path)
original=read(base/'before.json')
assert supplement['scope']=='SUPPLEMENTAL_POST_RUN_GIT_COMPARISON_NOT_ORIGINAL_BEFORE_CAPTURE'
assert supplement['execution_head']==original['execution_head']=='27ced22e73da7631d65bdd6e1844de24dd198065'
assert len(supplement['files'])==len({f['path'] for f in supplement['files']})==53
checked=[]
for f in supplement['files']:
    path=f['path']
    assert path.startswith(('evaluation/','qualification/core/')) and Path(path).suffix in ['.go','.json']
    assert path not in original['source_manifest']
    current=(root/path).read_bytes()
    blob=subprocess.run(['git','show',supplement['execution_head']+':'+path],cwd=root,capture_output=True,check=True).stdout
    assert len(current)==f['bytes'] and sha(root/path)==f['sha256']
    assert current==blob
    checked.append({'path':path,'sha256':f['sha256'],'bytes':f['bytes'],'current_equals_execution_git_blob':True})
assert supplement['all_worktree_bytes_match_execution_commit'] is True and supplement['source_modified'] is False
updated=read(out/'root-batches-review.json')
for path,h in updated['artifact_hashes'].items():assert sha(root/path)==h,path
updated['dependency_supplement']={
    'verdict':'PASS_POST_RUN_GIT_BYTES_COMPARISON_ONLY',
    'scope':supplement['scope'],'reference':supplement_path.relative_to(root).as_posix(),
    'sha256':sha(supplement_path),'execution_head':supplement['execution_head'],
    'files_verified':53,'original_before_capture':False,'files':checked,
    'limitation':'These 53 files were omitted from the original before manifest. Current bytes match the execution Git commit after execution; this cannot prove their bytes at test start or upgrade the original before capture. No test rerun, scope extension, or complete dependency closure claim.'}
updated['artifact_hashes'][supplement_path.relative_to(root).as_posix()]=sha(supplement_path)
(out/'root-batches-review.json').write_text(json.dumps(updated,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=out/'root-batches-review.md'
addition='''

补充依赖核查：新增 dependency-supplement.json 的 53 个 evaluation/qualification/core `.go`/`.json` 文件，逐项确认当前字节、SHA-256、大小与运行版本 `27ced22` 的 Git blob 一致；原始 raw/report/before 哈希保持不变。此证据明确为 `SUPPLEMENTAL_POST_RUN_GIT_COMPARISON_NOT_ORIGINAL_BEFORE_CAPTURE`。53 项都未出现在原始 before 清单中，因此属于运行后 Git 比对，不能追认运行开始时已捕获这些文件，也不能由此声称完整依赖闭包、扩大 case 验收或消除 R05 退出码未知限制。没有重跑测试。
'''
if addition not in md.read_text(encoding='utf-8'):md.write_text(md.read_text(encoding='utf-8')+addition,encoding='utf-8')
print(json.dumps({'dependency_supplement':'PASS_POST_RUN_GIT_BYTES_COMPARISON_ONLY','files':53,'original_before_capture':False}))
