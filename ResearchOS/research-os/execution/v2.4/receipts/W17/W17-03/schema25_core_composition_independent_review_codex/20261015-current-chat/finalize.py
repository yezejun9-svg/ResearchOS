import pathlib,json,hashlib,subprocess,collections,datetime
R=pathlib.Path('D:/作品集/ResearchOS/research-os');E=pathlib.Path(__file__).parent;A=R/'execution/v2.4/receipts/W17/W17-03/schema25_core_composition_source_codex/20261015-current-chat';W=R/'.local/worktrees/schema25-core-composition-20261015'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def pin(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def write(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
audit=read(E/'audit.json');fresh=[]
for label in ['fresh-host-boundary','missing-core-budget-release']:
 c=read(E/(label+'.json'));counts=collections.Counter();names=[]
 for line in pathlib.Path(c['stdout']['path']).read_text(encoding='utf-8').splitlines():
  x=json.loads(line)
  if x.get('Action') in ['pass','fail','skip'] and x.get('Test') and '/' not in x['Test']:counts[x['Action']]+=1;names.append([x['Action'],x['Test']])
 assert c['native_exit']==0 and c['source_unchanged'] and counts=={'pass':2}
 fresh.append(dict(receipt=pin(E/(label+'.json')),label=label,counts=dict(counts),names=names,overlay_only=label=='fresh-host-boundary'))
assert subprocess.check_output(['git','status','--porcelain=v1'],cwd=W)==b''
original=read(E/'main-original9-guard.json')
for x in original['files']:assert pin(R/x['path'])['sha256']==x['sha256']
assert pin(pathlib.Path(original['project_identity']['path']))==original['project_identity']
assert subprocess.check_output(['git','status','--porcelain=v1','--untracked-files=no'],cwd=R).decode().splitlines()==audit['main_tracked_status']
assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()=='4f4023c956f84d65743f39ce77d6c8899a21ada1'
native=[]
for f in (A/'T5-host-native-evidence').glob('*AcrossHeartbeatNative/canonical-evidence.json'):
 x=read(f);assert x['classification']=='NATIVE_SYNTHETIC_SECOND_PAUSE' and x['live_model_calls']==0 and x['heartbeat_wait_milliseconds']==17000
 assert x['heartbeat_after']>x['heartbeat_before'] and len(x['pause_intents'])==2 and len(x['activations'])==2 and x['final_run']['attempt']==1
 native.append(dict(file=pin(f),classification=x['classification'],heartbeat_wait_ms=17000,heartbeat_before=x['heartbeat_before'],heartbeat_after=x['heartbeat_after'],pause_count=2,activation_count=2,live_model_calls=0,actual_host_tool_calls=x['actual_host_tool_calls'],attempt=1))
for f in A.glob('T1-buildinfo-*.stdout.raw'):
 t=f.read_text(encoding='utf-8');assert 'vcs.revision='+audit['candidate'] in t and 'vcs.modified=false' in t
diagnostics=[dict(attempt=1,kind='REVIEW_AUDIT_SCRIPT_FAILURE',error='patch compare used --full-index while frozen author patch uses abbreviated indexes',resolution='match frozen diff --binary --no-ext-diff --no-textconv; exact bytes now verified',source_test_failure=False),dict(attempt=2,kind='REVIEW_AUDIT_SCRIPT_FAILURE',error='JSON scalar line in non-Go buildinfo output had no .get',resolution='only dictionary Go events counted; all29 receipts now audited',source_test_failure=False)]
write('diagnostic-ledger.json',dict(attempts=diagnostics,preserved=True))
scratch=E/'scratch';leftovers=list(scratch.iterdir()) if scratch.exists() else []
assert not leftovers,'review temporary leftovers require exact-path cleanup'
if scratch.exists():scratch.rmdir()
verdict='LIMITED_COMPOSED_SOURCE_ACCEPTANCE_WITH_OPEN_BASELINE_FIXTURE_FAILURE'
out=dict(schema='researchos.four-branch-composition-independent-source-review.v1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verdict=verdict,source=dict(base='4f4023c956f84d65743f39ce77d6c8899a21ada1',head=audit['candidate'],tree=audit['tree'],exact_changed_paths=audit['source_paths'],clean=True),audit=pin(E/'audit.json'),original9_guard=pin(E/'main-original9-guard.json'),original9_reference=pin(R/'execution/v2.4/receipts/W05/W05-99/current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json'),fresh_tests=fresh,reused_author_receipts=29,reused_author_verified_references=178,nested_host_files=20,full_tree_entries=36201,main_protected_count=10,original_main_protected_count=9,native_semantic_audit=native,source_findings=[],coverage_gap_resolved=dict(author_domain12='W06 plus pause/local launch tests omitted two previously accepted budget tests',new_current_candidate_two=['TestW12BudgetLeaseTakeover','TestCompletedRuntimeLocalLaunchRelease'],status='PASS_NEW_ATTEMPT_NOT_OLD_EVIDENCE'),open_findings=[dict(id='BASELINE_ACTIVE_QUEUE_FIXTURE',severity='P2',scope='historical source22 fixture branch',status='OPEN',evidence='Author T3 initial37PASS3FAIL; identical ActiveQueueRecovery failure on cleanMain4f at backup_configuration_upgrade_test.go:145 missing client_command_identities; no composition-only failure demonstrated. Unchanged failing fixture is not accepted or fixed.'),dict(id='T8_AND_PRODUCT_QUALIFICATION',status='NOT_ACCEPTED_NOT_RUN',scope='combined schema25 Native signed authority/pins, actual original migration, package/install, Desktop/live provider and formal cases',detail='Root reported actualMain4f MODEL1 HTTP200, TOOLrequest1 refused, actualTOOL0, RunRUNNING/dispatchUNKNOWN. Separate unresolved diagnosis; no replay or originaldata read here.')],historical_attempts=dict(T3_initial={'pass':37,'fail':3,'skip':0},T3_resources_corrected={'pass':2,'fail':0,'skip':0},T3_cleanMain_activequeue={'fail':1},queue_initial={'pass':1,'skip':2},queue_resource_corrected={'pass':3,'skip':0},failure_history_preserved=True),acceptance_boundary='Only exact53 Source composition and targeted isolated fixture/native-synthetic evidence. Not all tests green; baseline fixture failure remains open. No Main integration, deployment, fresh Native authority or actual migration accepted.',missing_object_boundary='Required scoped objects and candidate fulltree readable. Historical62 missing trees not re-audited or repaired. No GC/repack.',source_main_sharedstate_changes=False,formal_increment=0,formal_cases='0/42',parent_tasks_open=22)
write('review.json',out)
doc=f'''# 四支组合独立 Source 审查

结论：**{verdict}**。候选 `{audit['candidate']}`，tree `{audit['tree']}`。接受范围为 Main4f 上精确53文件的源码组合及限定夹具证据；历史 source22 fixture 失败保持 OPEN，不能称全部测试通过。

## 范围与保护

独立比对36,201个Git树条目、完整patch、53个文件的Git/工作区字节、四阶段前置blob和接受输入。唯一交叉 backup.go 保持 f809最终字节；storage9→Native22→Core21→Bridge2顺序正确。178个证据引用通过哈希核验，包含29个作者命令回执和20个Host嵌套证据文件。5个二进制记录均绑定本候选且 vcs.modified=false。

Main仍4f、20项tracked dirty、index为空；Main10保护文件与候选一致。原9按preflight-v2冻结的Main工作字节校验，无覆盖；候选不继承Main未提交修改。project_identity未变化。未写Source/Main/shared状态或产品数据。

## 生产边界与新验证

control主入口保持verifier dispatcher优先，其后Native私有入口必须验证继承authority；普通启动lease→verifier历史gate→store.Open顺序不变。backup同时绑定schema25验证和Native pause handoff，未把私有preserve callback扩成普通备份绕行。CheckMigrationSafety继续阻止已有24自动升25。Bridge legacy分支不能由V1降级进入。

作者T5实际12项与此前13项不是同一集合，漏了 TestW12BudgetLeaseTakeover 和 TestCompletedRuntimeLocalLaunchRelease。本审查在同一clean候选新跑两项，2PASS/0FAIL/0SKIP；没有把旧候选PASS当作新证据。

另以只读Go overlay加入两个独立测试，2PASS/0FAIL/0SKIP：schema25下verifier replacement仍以supported schema24 required拒绝、不改DB也不创建plan；在隔离schema24 fixture提交合法replacement后加入schema25标记，合法终态历史可通过startup gate，登记漂移仍被拦截且DB未改。这验证门禁关系，不是完整schema25迁移或安装证明。

新执行共2命令、4顶层PASS；已有T1–T7的29回执作为作者证据复核，不改称独立重跑。Host模型／工具第二暂停证据均为17秒等待、heartbeat推进、2暂停/2激活、同attempt1、live_model_calls=0的native synthetic轨迹，不能推导实际提供商资格。

## 未关闭项

- T3初始37PASS/3FAIL原样保留；两项历史程序资源失败补齐29项pin后各PASS。ActiveQueueRecovery在候选与cleanMain4f同145行因source22缺client_command_identities失败；该23表不属于22 fixture，历史支路保持OPEN，本审查未修改fixture或宣称其接受。
- Queue初始1PASS/2SKIP保留；同候选补资源新attempt为3PASS/0SKIP。
- 未执行T8新候选签名/pin授权、实际原库迁移、package安装或Desktop资格。旧f809授权不能复用为组合授权。Root现有Main4f资格运行MODEL1 HTTP200但TOOLrequest1拒绝、actualTOOL0、RunRUNNING/dispatchUNKNOWN，单独诊断中；本审查未读取或重放现场。
- 审查工具两次诊断失败已保留：patch格式参数不一致、非Go输出JSON标量解析；修正后审计通过，均非产品测试失败。历史清理拒绝、失败次数和62缺树状态未重置。仅清理本审查空scratch目录。

formal_increment=0；0/42；全部22父任务open。审查不签发Main整合、部署或实际迁移授权。
'''
(E/'review.md').write_text(doc,encoding='utf-8')
files=[pin(f) for f in sorted(E.iterdir()) if f.is_file() and f.name!='evidence-manifest.json']
write('evidence-manifest.json',dict(verdict=verdict,files=files,formal_increment=0))
print(json.dumps(dict(verdict=verdict,review=pin(E/'review.md'),json=pin(E/'review.json'),manifest=pin(E/'evidence-manifest.json')),ensure_ascii=True))
