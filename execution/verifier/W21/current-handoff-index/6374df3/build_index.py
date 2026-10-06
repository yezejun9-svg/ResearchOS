"""Read-only handoff inventory compilation; no product, test or provider execution."""
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]
SOURCE = '6374df33e95b5f64a53fab8c656d2486298cf57d'
inputs = {}
def read(rel):
    data = (ROOT / rel).read_bytes()
    inputs[rel] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    return json.loads(data.decode('utf-8-sig'))
def track(rel):
    data = (ROOT / rel).read_bytes()
    inputs[rel] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

A = 'execution/acceptance_status.json'
B = 'execution/bootstrap_ledger.json'
CP = 'execution/checkpoint.json'
T = 'spec/v2.0/contracts/tasks.json'
BASE = 'execution/verifier/W21/final-index-version-audit/f510491/'
R01 = 'execution/verifier/W21/current-domain-context/27ced22/review.json'
R05 = 'execution/verifier/W21/current-domain-context/27ced22/root-batches-review.json'
R03 = 'execution/verifier/W21/current-evaluation-policy/27ced22/review.md'
R04 = 'execution/verifier/W21/current-evolution-legacy/27ced22/review.json'
R02 = 'execution/receipts/W21/current-source-research/609837e/report.json'
A05 = 'execution/receipts/W21/current-source-research/609837e/a05-historical-binding.json'
UI = 'execution/verifier/W13/ui-recovery-c26/review.json'
UIROOT = 'execution/receipts/W13/c26-recovery/root-integration-3ed0fa2.json'
CLI = 'execution/resource_requests/RQ-W05-CLI-POLICY-001.json'
CUTOVER = 'execution/resource_requests/RQ-W17-LOCAL-CUTOVER-POLICY-001.json'
LICENSE = 'execution/verifier/W20/license-binding-provenance/1.2.11/review.md'
formal, ledger, checkpoint, tasks = read(A), read(B), read(CP), read(T)['tasks']
baseline = {x['case']: x for x in read(BASE + 'reuse-matrix.json')['cases']}
for rel in [BASE+'review.md', BASE+'reuse-subset-binding.json', R01, R05, R03, R04, R02, A05, UI, UIROOT, CLI, CUTOVER, LICENSE]:
    track(rel)
requests = [read(CLI), read(CUTOVER)]

# Entries describe only evidence already read and scoped. They do not issue case acceptance.
evidence = {}
def group(ids, state, observation, limit, refs, source):
    for case in ids.split():
        evidence[case] = {'current_evidence_state': state, 'observation': observation,
                          'unverified_or_failed': limit, 'current_refs': refs, 'evidence_source': source}
group('C01 C02', 'TARGETED_DELTA_ONLY', 'R01/R07 六个 selector 共34断言、exit0；本组 context/授权/项目隔离限定路径通过。',
      'C01冻结模型/parser仅历史复用，无新provider；未覆盖完整新增planning/research context。', [R01], '27ced22')
evidence['C02']['unverified_or_failed'] = '当前公开合成项目隔离/context矩阵有证据；未认证安装服务私有边界或完整传递依赖闭包。'
group('C03 C04', 'HISTORICAL_REUSE_CANDIDATE', '旧版本审计保留D04影响传播与权限回归候选。',
      'f510491范围建议未构成6374df3完整依赖闭包或当前整例重签。', [BASE+'review.md', BASE+'reuse-subset-binding.json'], 'f510491及其引用版本')
group('C05', 'CURRENT_REGRESSION_FIX_REVIEW_PENDING', '609837e当前manual no-adoption关闭回归失败，批次exit1；兼容修复和control_drain独立审查待冻结。',
      '历史PASS保留；当前不得PASS，不得放松monitor独立接受。只在修复正式冻结后补定位。', [R02, B], '609837e；修复PENDING')
group('C06', 'TARGETED_API_PASS_UI_PARTIAL', 'R02两项missing-X/429 coalescing通过；与三项A05离线检查合计13断言。',
      '整批exit1因C05；不是完整当前C06或新provider；界面资格独立。', [R02], '609837e')
group('C07 C08', 'PARTIAL_BATCH_WITH_FIXTURE_FAILURE', 'R03硬门/弃权子断言通过；第二次90语义断言PASS，但json-body fixture启动失败、Go exit1。',
      '第一次91断言PASS但Go退出码未保存；不得合成完整批次或case PASS。', [R03], '27ced22')
group('C09', 'HISTORICAL_REUSE_CANDIDATE', 'control76b原日志C09与3断言通过；f510491审计16相关文件不变。',
      '原同包另一setup失败仍FAIL；后续current-control/recovery变化未形成完整当前C09。', [BASE+'review.md', BASE+'reuse-subset-binding.json'], 'f510491及其引用版本')
group('C10 C12 C20', 'READ_ONLY_PARTIAL_COVERAGE', 'R04映射9项原断言；current-control无收益拒绝等子证据可限定复用。',
      'legacy篡改/退化回退/双rubric链未完整复验；没有执行native/private helper；历史PASS未升级。', [R04], '27ced22')
group('C11 C13 C14 C15 C16', 'TARGETED_RAW_PASS_EXIT_UNKNOWN', 'R05共11测试18断言、raw package PASS；公共budget/effect/retention/checkpoint子证据。',
      'Go OS退出码未知，wrapper exit1；53文件为运行后补比对，不是原before capture；非完整case。', [R05], '27ced22')
group('C17 C18', 'BOUNDED_BROWSER_REUSE', 'UI冻结证据保留通知去重/精确成果链及4/6→4/9旧投影拒绝观察，root绑定292源/64证据。',
      '五轮runner均exit1 FAIL；仅同产品字节下相应子项复用，不重签完整UI case。', [UI, UIROOT], '1150137；root集成3ed0fa2')
group('C19 A06', 'TARGETED_DELTA_WITH_HISTORY', 'R07来源区分、依赖链失效、HTTP context当前7断言通过（R01/R07合批exit0）。',
      'junction/root identity/fallback/cache保留历史证明；无完整当前A06重验或native根边界重跑。', [R01], '27ced22')
group('C21 A07', 'HISTORICAL_REUSE_CANDIDATE', '旧审计复用S2 consumer/I2 W10NativePair及25选定文件字节匹配。',
      '外层native SOURCE失败保留；当前依赖闭包未知，不升级LIVE或完整case。', [BASE+'review.md', BASE+'reuse-subset-binding.json'], 'f510491及其引用版本')
group('C22', 'HISTORICAL_REUSE_CANDIDATE', '旧审计30相关文件不变及S2 consumer-tool-binding子检查可限定复用。',
      '同用户fixture不等当前安装服务资格；未重跑被终止S2 adversarial。', [BASE+'review.md', BASE+'reuse-subset-binding.json'], 'f510491及其引用版本')
group('C23 C24 C25', 'HISTORICAL_UI_WITH_PARTIAL_DELTA', '历史正式UI接受保留；I1前15项及单独resources320修复按旧审计限定复用。',
      '原core整体FAIL，后半段状态/键盘焦点/预览等未全复验；C26子集不补齐这三例。', [BASE+'review.md', UI], '历史UI及1150137有限子集')
group('C26', 'PARTIAL_BROWSER_NOT_ACCEPTED', '8有限观察/1降级/2未验证；两次silent45009ms、水位1→2；idle47秒3heartbeat/GET28不变。',
      '五轮exit1；实际freeze/OSsleep/同项目迟到帧未证；最终15秒helper NOT_RUN；正式NOT_RUN不改。', [UI, UIROOT], '1150137；root集成3ed0fa2')
group('A01', 'HISTORICAL_REUSE_CANDIDATE', '旧审计5个导入/规格相关文件不变，原导入限定语义可候选复用。',
      '不是完整依赖闭包，不依据历史直接签6374df3当前PASS。', [BASE+'review.md', BASE+'reuse-subset-binding.json'], 'f510491及其引用版本')
group('A02 A03', 'TARGETED_DISPATCH_ACCEPTANCE_ONLY', 'R08共9测试54断言，实际Go exit0；当前普通调度/重复派发/独立接受边界。',
      '不能代替全接口与完整真实执行链；未重试旧native/S2/CLI阻塞分支。', [R05], '27ced22')
group('A04', 'BLOCKED_RESOURCE', 'RQ-W05仍OPEN：授权CLI工具命令在启动前被policy拒绝，两次探针后停重试。',
      '需受支持授权执行能力后完成受影响启动/产物/取消/恢复全链；model-only和synthetic不替代。', [CLI], '历史资源请求，当前仍OPEN')
group('A05', 'OFFLINE_BINDING_WITH_HISTORICAL_LIVE', 'R02三项来源封存/游标/HTTP离线检查通过；原LIVE产物完整性与adapter连续性单列。',
      '无新供应商调用、freshness或native SOURCE桥证明；批次仍exit1。', [R02, A05], '609837e；原LIVE6773532')
group('A08', 'PURE_PUBLIC_BINDING_ONLY', 'R03共48纯公开绑定断言通过，原summary与当前receipt/key/FAILED-ADVISORY-NONE绑定成立。',
      '不读私有标签、不重评、不证明当前安装服务freshness；每键30/15不足60/30，authority NONE。', [R03], '27ced22；原LIVE d6acd16')
group('A09', 'HISTORICAL_REUSE_CANDIDATE', '旧审计D04来源冲突7断言与12文件子集支持历史生命周期限定复用。',
      '新增研究/规划路径不属于旧case；W15真实W14输入仍未闭合。', [BASE+'review.md', BASE+'reuse-subset-binding.json'], 'f510491及其引用版本')
group('A10 A11', 'NOT_RUN_WITH_ACTIVATION_RESOURCE', '远程/权限历史fixture与隔离迁移子证据保留；RQ-W17 activation仍OPEN。',
      '当前安装版本、真实手机配对/撤销/重连资格未完成；仅支持的授权恢复可解除，禁止绕过policy。', [CUTOVER, B], '历史fixture及资源请求')
group('A12', 'TARGETED_STORAGE_RECOVERY_ONLY', 'R09共2测试19断言、Go exit0；公共合成旧数据恢复及继续子链。',
      '不是current-control恢复授权；schema20机制不等完整当前A12或W18阶段接受。', [R05, B], '27ced22')
group('A13', 'NOT_RUN_UPSTREAM_LIVE_OPEN', 'W14-G01历史fixture接受，真实研究闭环未接受。',
      '需W08/W09/W10/W11/W12/W13依赖及真实来源/Jev/必要实验全链；W05执行器仍阻塞。', [B, CLI, T], '当前施工索引')
group('A14', 'NOT_RUN_OVERNIGHT_RESTART', 'W19未开始，未有完整真实隔夜/Windows重启资格。',
      '需W14/W17/W18闭合、实际故障计划/持续窗口/恢复证据；不能用等待或fixture补成。', [B, T], '当前施工索引')
group('A15', 'PACKAGE_REFRESH_PENDING_CLEAN_WINDOWS_OPEN', '已有旧有界包审查；本轮新包待C05冻结及打包，随后独立existing fixture一次。',
      '干净Windows安装/更新/保留数据卸载与其余41例未闭合；有界包≠正式发行。', [B, CP, LICENSE], '最终包PENDING')
group('A16', 'PARTIAL_FIXTURE_NO_RELEASE_AUTHORITY', '历史fixture及current-control无收益拒绝保留；正式PARTIAL。',
      '需当前恢复资格、独立supervisor/真实canary切换回退/host restart/观察窗口；缺恢复授权不执行。', [B, R04, T], '历史接受及27ced22限定审查')
assert len(evidence) == 42 and set(evidence) == set(formal['cases'])
rows = []
for case, historic in formal['cases'].items():
    for ref in historic.get('evidence', []):
        assert (ROOT / ref).is_file(), ref
    rows.append({'case': case, 'title': baseline[case]['title'],
                 'historical_formal': historic, 'required_mode': baseline[case]['required_mode'],
                 'formal_state_ref': A + '#/cases/' + case,
                 'baseline_reuse_ref': BASE + 'reuse-matrix.json#case=' + case,
                 **evidence[case], 'current_complete_case_pass': False, 'formal_verdict_reissued': False})

conditions = {
 'W05':'W05-G02/A04：受支持的授权CLI真实工具能力恢复，完成启动/产物/取消/恢复；不重试已拒策略。',
 'W06':'W06-G03：W05真实资格闭合后，真实报告→独立verifier→接受→后继链。',
 'W08':'先完成当前C05兼容修复和独立冻结审查，保留monitor硬门；W05/W06 LIVE依赖仍须闭合。',
 'W10':'已有G01/G02/G03及A07/C21不等整阶段；须W06/W05 LIVE资格与当前接口整合。',
 'W11':'已有四子门与A08初始评估接受，但W10等上游未闭；不足样本键保持FAILED/ADVISORY/NONE。',
 'W12':'W12-G02真实检查点/恢复/用量与未知费用链，须W06/W05 LIVE能力；R05退出码未知保留。',
 'W13':'W13-G03/C26真实恢复缺口及上游W06/W08/W12闭合；有限browser证据不补正式资格。',
 'W14':'W14-G02/A13真实研究闭环；三来源/Jev/实验及所有上游阶段资格闭合。',
 'W15':'W15-G02使用真实W14资料生成/试用候选，依赖运行资格闭合；现有A09不自动闭阶段。',
 'W16':'W16-G01当前有效恢复前提及G03/A16真实独立supervisor/canary/回退/重启窗口；新恢复授权仍缺。',
 'W17':'G01剩余A11与G02当前安装版本/真实手机；支持的credential issuance/activation恢复且复核源漂移。',
 'W18':'当前备份→隔离恢复→继续运行证据与W12/W05 LIVE资格闭合；合成恢复不授予control authority。',
 'W19':'先闭W14/W17/W18，冻结故障/停止计划后完成真实持续隔夜和Windows重启恢复。',
 'W20':'本轮新包PENDING；另需其余41正式例、A15干净Windows、11页面最终真实API、许可/native notice缺口闭合。',
 'W21':'W20及所有阶段依赖、42正式例当前完整有效；真实Outcome/Jev模式/费用时间可靠性基线审查。',
}
task_by_id = {x['task_id']: x for x in tasks}
closed = {k for k, v in ledger['tasks'].items() if v['status'] == 'CONSTRUCTION_ACCEPTED'}
def ancestors(task):
    result = set(task_by_id[task]['depends_on'])
    for d in list(result): result |= ancestors(d)
    return result
wbs = []
for task in tasks:
    tid = task['task_id']
    state = ledger['tasks'][tid]
    refs = [B + '#/tasks/' + tid, T + '#task_id=' + tid]
    for acceptance in ledger['external_verifier_acceptances']:
        if isinstance(acceptance, dict) and acceptance.get('task_id') == tid:
            ref = acceptance.get('reference')
            if ref: refs.append(ref)
    for ref in refs:
        assert (ROOT / ref.split('#')[0]).is_file(), ref
    wbs.append({'task_id':tid, 'title':task['title'], 'ledger_status':state['status'],
                'whole_stage_closed_in_ledger':tid in closed, 'direct_dependencies':task['depends_on'],
                'unclosed_direct_dependencies':[x for x in task['depends_on'] if x not in closed],
                'unclosed_transitive_dependencies':sorted(ancestors(tid) - closed),
                'owned_cases':task['owned_acceptance_ids'], 'gate_ids':[x['check_id'] for x in task['task_gate_checks']],
                'ledger_record':state, 'necessary_resume_condition':conditions.get(tid,'历史施工接受记录保留；本索引未重新认证当前全版本，相关新变动另按限定证据复核。'),
                'evidence_refs':refs})
assert len(wbs) == 22

summary = {'kind':'PREPARATORY_HANDOFF_INDEX_NOT_W21_G01_ACCEPTANCE', 'index_source':SOURCE,
           'historical_counts':dict(Counter(x['historical_formal']['status'] for x in rows)),
           'case_rows':42,'wbs_rows':22,'historically_closed_wbs':len(closed),'unclosed_wbs':22-len(closed),
           'current_complete_34_pass_claimed':False,'formal_state_changed':False,'tests_executed':False,
           'dependency_closure_of_targeted_evidence':'UNKNOWN_NOT_CERTIFIED',
           'pending_final_locations':{'C05':'PENDING_FIX_SOURCE_AND_INDEPENDENT_REVIEW_FREEZE',
                                      'package':'PENDING_FINAL_ZIP_FREEZE_AND_ONE_EXISTING_RELEASE_FIXTURE'},
           'next_update_scope':'Only append final C05 and package locations; do not regenerate all index or replay old cases.',
           'resource_requests':requests,'cases':rows,'wbs':wbs,
           'authority_note':'Resume conditions record necessary prerequisites only; they do not authorize blocked actions.'}
save('index.json', summary)
save('input-manifest.json', {'source':SOURCE,'files':inputs})
save('final-locations.json', {'basis':'6374df3 immutable preparatory snapshot; only these two entries may be supplemented later',
    'C05':{'status':'PENDING_FIX_SOURCE_AND_INDEPENDENT_REVIEW_FREEZE','reference':None},
    'package':{'status':'PENDING_FINAL_ZIP_FREEZE_AND_ONE_EXISTING_RELEASE_FIXTURE','reference':None}})
lines = ['# 42 项交接预备索引','',
         '历史正式状态来自 acceptance_status；当前列只表示已有子证据。所有行 current_complete_case_pass=false，不签 W21-G01。', '',
         '| Case | 历史正式 / 模式 | 当前已有证据 | 未验证、失败或资源条件 | 引用 |',
         '| --- | --- | --- | --- | --- |']
for x in rows:
    hs=x['historical_formal']; refs=[x['formal_state_ref'], *x['current_refs']]
    links='；'.join('['+('历史' if i==0 else '证据'+str(i))+']('+str(ROOT / ref.split('#')[0]).replace('\\','/')+')' for i,ref in enumerate(refs))
    lines.append(f"| {x['case']} {x['title']} | {hs['status']} / {hs.get('mode') or '('+x['required_mode']+')'} | {x['observation']} | {x['unverified_or_failed']} | {links} |")
(OUT/'cases.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
lines=['# 22 个 WBS 依赖与恢复条件','','仅 CONSTRUCTION_ACCEPTED 记为历史整阶段已接受；有限子门、已有 case 和开发结果不闭合依赖。完整直接及传递依赖在 index.json。', '',
       '| WBS | 台账状态 | 直接未闭依赖 | 必要恢复条件 | 引用 |','| --- | --- | --- | --- | --- |']
for x in wbs:
    links='；'.join('[依据'+str(i+1)+']('+str(ROOT/ref.split('#')[0]).replace('\\','/')+')' for i,ref in enumerate(x['evidence_refs']))
    lines.append(f"| {x['task_id']} {x['title']} | {x['ledger_status']} | {', '.join(x['unclosed_direct_dependencies']) or '无'} | {x['necessary_resume_condition']} | {links} |")
(OUT/'wbs.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['cases','wbs','resource_requests']},ensure_ascii=False))
