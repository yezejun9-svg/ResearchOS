import hashlib,json,pathlib,subprocess,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os');E=pathlib.Path(__file__).parent
Q=R/'execution/v2.4/receipts/W17/W17-03'
MAIN='4f4023c956f84d65743f39ce77d6c8899a21ada1';OLD='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';STORAGE='d17acc0e128d8438e530ffafc8d704d15b3dd500';BASE='60f8c81a7529081eb51d525ab913d63102148a46'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git',*args],cwd=R)
def paths(a,b):return git('diff','--name-only',a,b).decode().splitlines()
def blob(commit,path):
    row=git('ls-tree','-z',commit,'--',path).decode()
    if not row:return None
    mode,kind,tail=row.split(' ',2);oid=tail.split('\t',1)[0]
    assert kind=='blob'
    raw=git('cat-file','blob',oid)
    return dict(blob=oid,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))

storage=read(Q/'root_schema25_source_codex/20261014-current-chat/report.json')
native_scope=read(Q/'schema24_to25_source_codex/20261014-current-chat/scope.json')
core=read(Q/'mu_m1_02_independent_review_codex/20261014-current-chat/cumulative-review/final-report.json')
bridge=read(Q/'bridge_checkpoint_compat_source_codex/20261014-current-chat/source-manifest.json')
defs=[('storage25',storage['base_commit'],STORAGE,[x['path'] for x in storage['source9']]),('native25',BASE,'f80955594bdd0373ae1c961cd02ab6be96f2c196',native_scope['paths']),('core',BASE,core['source']['head'],[x['repo_path'] for x in core['source']['sources']]),('bridge',OLD,bridge['source_commit'],[x['path'] for x in bridge['source']])]
stages=[];current={};members={};blocked=[]
for name,base,head,allow in defs:
    try:
        assert sorted(paths(base,head))==sorted(allow)
        stage=dict(name=name,base=base,base_tree=git('rev-parse',base+'^{tree}').decode().strip(),head=head,tree=git('rev-parse',head+'^{tree}').decode().strip(),scope_count=len(allow),files=[])
        for p in sorted(allow):
            old=blob(base,p);new=blob(head,p);main=blob(MAIN,p)
            before=current.get(p,main)
            action='APPLY_EXACT_ACCEPTED_DELTA' if before==old else 'ALREADY_IDENTICAL' if before==new else 'REQUIRES_MERGE_REVIEW'
            stage['files'].append(dict(path=p,base=old,candidate=new,main=main,expected_before=before,action=action))
            members.setdefault(p,[]).append(name)
            if action!='REQUIRES_MERGE_REVIEW':current[p]=new
        stages.append(stage)
    except (subprocess.CalledProcessError,AssertionError) as e:blocked.append(dict(branch=name,error=str(e),action='BLOCK_ONLY_THIS_BRANCH_NO_GC_OR_REPAIR'))
mainpaths=paths(OLD,MAIN)
protected=[dict(path=p,main=blob(MAIN,p),overlaps_scoped_sources=p in members) for p in mainpaths]
assert all(not x['overlaps_scoped_sources'] for x in protected)
assert len(current)==53 and len(mainpaths)==10 and not blocked
assert all(x['action']!='REQUIRES_MERGE_REVIEW' for s in stages for x in s['files'])
for item in storage['source9']:assert blob(STORAGE,item['path'])['sha256']==item['sha256']
for item in bridge['source']:assert blob(bridge['source_commit'],item['path'])['sha256']==item['sha256']
for item in core['source']['sources']:assert blob(core['source']['head'],item['repo_path'])['sha256']==item['sha256']
refs=[Q/'root_schema25_source_codex/20261014-current-chat/report.json',Q/'root_schema25_independent_review_r4_codex/20261014-current-chat/report.md',Q/'schema24_to25_source_codex/20261014-current-chat/scope.json',Q/'schema24_to25_source_codex/20261014-current-chat/revision01/manifest.json',Q/'schema24_to25_independent_review_codex/20261014-current-chat/revision01/FINAL-report.json',Q/'mu_m1_02_independent_review_codex/20261014-current-chat/cumulative-review/final-report.json',Q/'mu_m1_02_independent_review_codex/20261014-current-chat/cumulative-review/evidence-manifest.json',Q/'bridge_checkpoint_compat_source_codex/20261014-current-chat/source-manifest.json',Q/'bridge_checkpoint_compat_independent_review_codex/20261014-current-chat/FINAL-report.json']
native_review=read(refs[4]);bridge_review=read(refs[8])
assert native_review['head']==defs[1][2] and native_review['status']=='SOURCE_ACCEPTED_P2_CLOSED_NATIVE_TRIAL_READY'
assert bridge_review['head']==defs[3][2] and bridge_review['status']=='SOURCE_ACCEPTED_LIMITED'
assert core['verdict']=='LIMITED_CUMULATIVE_SOURCE_ACCEPTANCE'
tests=[
dict(id='T1',scope='Build and source guards',required='Build combined control/backup/recovery-root/enrollment/runtime-verifier from clean combined candidate; run diff check and validate exact53 changed files, all 10 Main protected blobs, embedded/schema SQL equality. No installation/startup on actual data.'),
dict(id='T2',scope='Main c8 + verifier',required='Run tests/ui/desktop/coding-authorization-boundary.test.mjs and existing verifier replacement parser/journal/crash/causality tests. Verify main dispatcher precedence and startup gate before store.Open unchanged; schema25 replacement remains refused.'),
dict(id='T3',scope='Storage + Native backup overlap',required='Run schema25 pause storage/backup validator cases, old prepared23to24 regressions, new pause handoff and signed Destination-parent staging negatives; public backup+restore schema24/25 fixture round trips. Validate internal/domain/backup.go preserves both pause validator and pause handoff behavior.'),
dict(id='T4',scope='Combined CLI entrypoints',required='Run TestPausePrivateControlRejectsBeforeNormalStartup and TestPausePrivateControlRejectsAmbiguousPathsBeforeDBOpen together with verifier replacement CLI tests; no authority means no DB open/listener. Normal startup pending/invalid replacement history remains blocked.'),
dict(id='T5',scope='Core + changed Bridge',required='Run current Core pause13 domain cases and Host8 native cases on combined binary with frozen M1 assets; model/tool second pause crosses17s, full rollback, exact queue and each-epoch budgets; same Run/attempt; no skip.'),
dict(id='T6',scope='Bridge legacy/V1',required='Run bridge legacy route7-leaf/V1 controls and existing TestRuntimeCoordinatorCheckpointResume + TestRuntimeCoordinatorCheckpointCrashRecovery on combined Core, proving legacy native_resume=false and V1 never fallback. Ordinary queue3 regressions remain passing.'),
dict(id='T7',scope='Fresh isolated schema25 startup',required='Use fresh fixture data only to check schema bootstrap and Core pause capability. Verify malformed25/future26 rejection and restore fence preservation. This is not installed DB24 migration acceptance.'),
dict(id='T8',scope='Later Native/package gates',required='Combined executable hashes differ from all frozen native/rehearsal release pins; rebuild evidence and separately obtain Root-authorized fresh signatures/configs before any native migration execution. Package/runtime/actual Desktop/live provider/formal acceptance remain separate and pending.')]
out=dict(schema='researchos.four-branch-composition-impact-map.v1',status='BOUNDED_COMPOSITION_SCOPE_PROPOSAL_ONLY_NOT_ACCEPTED',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),main=dict(head=MAIN,tree=git('rev-parse',MAIN+'^{tree}').decode().strip(),protected=protected),input_corrections=[dict(input_storage='d17acc0e128d8438e530ffafc8d704d15b3dd5009',verified_storage=STORAGE,actual_storage_base=storage['base_commit'],explanation='Input contained extra trailing9; frozen source manifest exact9 is based on c465, not a7ec. Core/Native base60 composes a7ec+same storage9.')],stages=stages,dependency_edges=[['storage25','native25'],['storage25','core'],['core','combined-native-pause-validation'],['bridge','combined-native-pause-validation']],overlaps=[dict(path=p,branches=v) for p,v in members.items() if len(v)>1],textual_conflicts=[],semantic_boundaries=[dict(id='VERIFIER_SCHEMA24_ONLY',file='internal/host/runtime_verifier_replacement_windows.go:285',requirement='Preserve strict schema24 preflight. No automatic extension to25. A valid terminal history can remain acceptable to startup gate, but replacement operation after upgrade remains unsupported.'),dict(id='PRIVATE_ENTRY_ORDER',file='apps/control/main.go:34',requirement='Keep Main verifier dispatcher first, then Native-expanded prepared recovery dispatcher; ordinary startup lease/history gate remains before DB open. Do not move authority checks to normal flags.'),dict(id='BINARY_PIN_REFRESH',requirement='Four-source composition invalidates previously built Native program and signed-release hashes as evidence for combined binaries; never relabel old pins.'),dict(id='BRIDGE_CORE_INTEGRATION',requirement='Bridge independently closed old legacy regressions, Core independently passed V1. Neither proves their combined runtime until T5/T6.')],bounded_builder_scope=dict(start_from=MAIN,source_paths=sorted(current),path_count=53,protected_main_paths=mainpaths,no_whole_branch_tree_overlay=True,expected_final_blobs=current,order=['storage25 exact9','native25 exact22','core cumulative21','bridge exact2'],backup_go_final_source=defs[1][2],extra_source_paths_allowed=False,authorization='This map is not builder/merge/deploy/data authority; Root must issue bounded composition scope.'),required_tests=tests,inputs=[pin(p) for p in refs],blocked_branches=blocked,missing_object_policy='No missing tree/blob encountered for required scoped reads. No GC/repack/repair attempted. Historical missing62trees not re-audited or cleared.',formal_increment=0,formal_cases_accepted='0/42',all_parent_tasks_open=22)
write(E/'COMPOSITION-MAP.json',out)
rows=[]
for s in stages:
 for x in s['files']:rows.append('| '+s['name']+' | '+x['path']+' | `'+x['candidate']['sha256']+'` | '+x['action']+' |')
doc='''# 四支 Source 与 Main4f 的精确组合影响图

结论：可形成 **从 Main4f 开始、精确53个文件** 的隔离组合施工范围。按各支真实基底核对，所需文件全部可读取，53文件均满足前置字节匹配，**无文本合并冲突**。唯一跨支同文件是 internal/domain/backup.go，必须先storage25后Native25。没有创建组合候选，也没有运行组合测试；本报告不是组合接受。

## 基线和接受范围

Main `4f4023c956f84d65743f39ce77d6c8899a21ada1`，tree `3db13a15cc52b2b0bd75cae3452c66509a9f55c9`。

| 支路 | 实际base | 接受的HEAD | tree | 范围/接受边界 |
|---|---|---|---|---|
| storage25 | c465d1356480d6e6a90da84656724f9fc02b31c7 | d17acc0e128d8438e530ffafc8d704d15b3dd500 | 0b182d56b6f5c76b3c80f0f4aeea38a384544dba | exact9，R4 SOURCE_FIXTURE_ACCEPTED |
| Native25 | 60f8c81a7529081eb51d525ab913d63102148a46 | f80955594bdd0373ae1c961cd02ab6be96f2c196 | 5bce20214223e8292f16a117a83407f52b4bca4a | cumulative22，6文件修订闭合TEMP问题，Source接受 |
| Core | 60f8c81a7529081eb51d525ab913d63102148a46 | 8f50cb57ff821554aef17e9a9bd5208935489d50 | 361ead86ee812d5e040fe1d2cde2a92297eb639f | cumulative21，限定累计Source接受 |
| Bridge兼容 | a7ec7ebf2d53848ea163b6115667b3e3761a6bd2 | 0f9a870aed72785297a9999396fc8c760b296e13 | fa071c9be7e39628c0b86ad43f77d5c50be63c7c | exact2，SOURCE_ACCEPTED_LIMITED |

任务文本storage hash末尾多了9，已用冻结report与Git确认上表40位hash。storage实际基底是c465；60f8c是a7ec加同一storage9的隔离组合。四支scope/manifest和接受报告已绑定在JSON inputs中。Native旧22文件报告曾NEEDS_REVISION，revision01明确闭合该问题，不能只拿旧报告或末6文件冒充累计范围。

## 给builder的边界

1. 从Main4f建立新的隔离候选，保留其全部现状；先应用storage9的确切delta，再Native22，再Core21，最后Bridge2。Core与Native彼此文件不重合，Bridge与其余支均不重合。
2. internal/domain/backup.go先取得storage的schema25 validator版本，再应用Native的publicPauseUpgradeHandoff/preservePauseUpgradeWorkspaces delta；最终完整字节应等于f809的该文件。禁止用storage版本最后覆盖它。
3. 只允许JSON bounded_builder_scope.source_paths中的53个文件；每文件base/candidate/Main/expected_before的blob、SHA-256和字节数均已列明。新增文件的base=null。若实际前置不再匹配，停止对应支路并回报，不能扩写文件。
4. Main自a7ec以来的10个文件与四支白名单完全不交叉，全部要求原blob不变：其中c8的desktop-management与coding-authorization测试，及c5/4f的control入口、verifier实现/日志/崩溃与参数测试。不得将任何oldbase分支整树覆盖到Main；那会回退profile验证并删除verifier功能。

## 语义交叉与必须保持的门

- **control入口**：Main apps/control/main.go原样保留。runRuntimeVerifierReplacement先分派；其后runPreparedRecoveryMaintenance由Native文件扩展PauseMigrationArgument。普通启动取得DataRootLease后仍先调用runtimeVerifierReplacementStartupGate，再store.Open；不能以新增迁移入口为由删除或挪后gate。Native私有入口仍必须先验证继承authority，不能落入普通启动。
- **verifier只支持schema24**：internal/host/runtime_verifier_replacement_windows.go:285明确要求完整1..24；组合不得擅自放宽到25。startup gate验证replacement历史链/当前安装记录，本身没有schema24检查，二者不能混为一谈。升级到25后再做verifier replacement尚不支持；需要独立范围和证明，或者在另行批准的运行计划中处理操作次序。本图不授权任一操作。
- **新二进制身份**：组合后control/backup/root/enrollment/verifier哈希均须重建核验。此前f809的程序pin、签名release、grant/config只能证明旧候选，不能复制为组合运行授权。
- **Core与Bridge**：Bridge支已独立使两项旧inline回归通过，Core支已独立验证V1两轮暂停；合并后仍需同一候选同时跑两组。Core原报告的旧依赖问题不能凭文件拼接直接宣布关闭。
- **schema25**：storage提供三表及backup validator，Core依赖其receipt/CAS/activation；Native提供受限24→25入口。源码齐备不证明实际迁移或普通安装包兼容，不能对真实data启动试验。

## 必须的组合验证

JSON required_tests给出T1–T8精确目的：53文件与Main10保护检查及组合程序构建；c8 profile/4f verifier参数、因果日志和crash回归；storage+Native旧23→24及新pause备份/restore/staging边界；两个private入口与普通startup gate；Core13 domain+Host8 native（17秒模型/工具、完整rollback、queue/预算）；Bridge legacy+V1和原两项checkpoint回归及普通queue3；fresh fixture schema25启动/restore；另行授权后的新pin Native/package门。

这些测试是待执行要求，不是本报告PASS。没有读取产品数据、运行package、签名、迁移、改Main/Source/shared状态。历史失败/清理拒绝保留；本次所需对象读取没有遇到缺树，不能据此声称历史62缺树已修复。若后续缺对象，仅阻塞对应支路，禁止GC/repack/替换对象。

formal_increment=0；0/42，22父任务open。

## 精确文件表

| 支路 | 文件 | 接受版本SHA-256 | 预期操作 |
|---|---|---|---|
'''
(E/'COMPOSITION-MAP.md').write_text(doc+'\n'.join(rows)+'\n',encoding='utf-8')
write(E/'evidence-manifest.json',dict(status=out['status'],files=[pin(E/n) for n in ['build_map.py','COMPOSITION-MAP.md','COMPOSITION-MAP.json']],formal_increment=0))
print(json.dumps(dict(unique_paths=len(current),overlaps=out['overlaps'],protected_main=len(protected),blocked=blocked,report=pin(E/'COMPOSITION-MAP.md'),map=pin(E/'COMPOSITION-MAP.json'),manifest=pin(E/'evidence-manifest.json')),ensure_ascii=True))
