import datetime,hashlib,json,pathlib,re
E=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def ref(p):return dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
a=read(E/'audit.json');post=read(E/'inputs.after.json');test=read(E/'test-summary.json');acl=read(E/'fresh-acl.json');clean=read(E/'cleanup-result.json')
assert a['status']=='PASS' and post['drift']==[] and test['counts']['pass']==214 and acl['pass'] and clean['removed']==20 and clean['remaining']==[]
observations=[read(p) for p in (E/'package-cases').rglob('observations.json')]
allchildren=[c for row in observations for c in row['children']]
real=[c for c in allchildren if c.get('spawnfile','').startswith('C:\\Users\\yqyyds\\.codex\\researchos-resource-cache\\normal-coding-profile-c8b7adab-20261014\\')]
assert real and all(c['exitCode']==0 and c['closed'] and c['exited'] and c['stdoutClosed'] and c['stderrClosed'] and c['stdinClosed'] for c in real)
assert all(row['external']==0 and row['model']==0 for row in observations)
matched=0
for p in (E/'package-cases').rglob('child-*.stdout'):
    if not p.stat().st_size:continue
    try:obj=read(p)
    except (ValueError,UnicodeError):continue
    if isinstance(obj,dict) and obj.get('build_input_digest')==a['input_digest']:matched+=1
put('runtime-evidence-summary.json',dict(observation_files=len(observations),all_child_records=len(allchildren),actual_packaged_validator_records=len(real),actual_packaged_children_exit0_and_all_handles_closed=True,child_outputs_with_new_binding=matched,fixture_external_and_model_zero=True,negative_child_copies_are_synthetic=True))
put('reviewer-diagnostics.json',dict(product_or_test_failures=0,read_only_setup_diagnostics=[dict(action='Attempt to read optional author FINAL-report.json',result='File absent; author frozen deliverable is FINAL-manifest.json',native_exit=0,powershell_nonterminating_error=True),dict(action='Batched rg included non-existent wire-harness.mjs',result='Read the actual harness in http-wire-boundary.test.mjs',native_exit=1),dict(action='Python metadata read without explicit UTF-8',result='JSON parse failed under default Windows encoding; repeated with -X utf8 and explicit encodings',native_exit=1)],acl_serialization_warning='PowerShell expanded SecurityIdentifier deeply; complete scalar SID and exact SDDL are retained; validation passed.',author_failures_preserved=3,author_failure_breakdown='2 ACL setup failures and 1 read-only path diagnostic; no failures erased'))
report=dict(schema='researchos.desktop-profile-package-independent-review/1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='codex:/root/attach_review_resume',role='independent package reviewer; implementation author is codex:/root/coding_profile_fix',model='inherited agent model; no new model choice',verdict='APPROVE_FOR_ROOT_NORMAL_REOPEN',findings=[],source_commit='c8b7adab9f0c15eb33f235f8d0d9eb205794e376',source_tree='cd951533206a6a4545a6e55fec374e62289d2dd4',package_root='C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-profile-c8b7adab-20261014',author_final_manifest_sha256='0bedb06fbb120c69c2224f0102c2be0c0aeed158d0f62322d7a9406a83351466',scope_sha256='74f119940664f9d1e41489f7cca3690c25add7d9d9c12a8011c0a20a64fb42a0',checks=a,fresh_non_GUI_tests=test['counts'],test_process=read(E/'fresh-package-cases.process.json'),input_drift=post,ACL_live_readback='PASS current SID owner, protected DACL, one explicit FullControl ACE',core_verifier_source='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2',mu_source='8dfebe36508ac0c2508735bb866756dab9283e74',migrations=list(range(1,25)),fresh_GUI=False,real_product_API_calls=0,product_DB_operations=0,model_calls=0,CONFIRM_calls=0,formal_increment=0,limitations=['214 cases use public loopback fixtures; no real Core/API/provider or GUI acceptance','Main/preload code imported from fixed clean source is byte-identical to package; validator executes from actual package with package cwd','Core/verifier and Mu binaries are reused, not rebuilt at c8b7adab','Native25/storage25/bridgecompat/Core17 changes are not included','Root alone may reopen the normal package against the existing authorized data location and verify persisted profile mc3f932/c671505 without another coding CONFIRM','This review grants no W05/Main24/formal-case closure'],cleanup='20 run-specific negative fixture roots removed after checked path and alias containment; raw evidence retained',source_stop_read_at=post['at'])
put('FINAL-report.json',report)
md=f'''# Desktop Profile 修复包独立审查

结论：**APPROVE_FOR_ROOT_NORMAL_REOPEN**。冻结的包可由 Root 按既定范围正常重开；本审查未发现阻塞项。

审查对象是 `normal-coding-profile-c8b7adab-20261014`，固定 source `c8b7adab9f0c15eb33f235f8d0d9eb205794e376` / tree `cd951533206a6a4545a6e55fec374e62289d2dd4`。作者 FINAL-manifest 的 SHA256 为 `0bedb06fbb120c69c2224f0102c2be0c0aeed158d0f62322d7a9406a83351466`，与委派输入一致。

独立重算 6,444 个构建输入，摘要为 `819e8a98f8b678928a6354663747ea2d0b7adab21bc220fe6720edf7dc20c8ce`。58 个包成员完整；14 个 Main/preload 文件与固定源码逐字节相同，3 个 React 资产与新构建输出相同。descriptor、编译 argv、binary Go buildinfo 中的输入绑定一致，validator 的 VCS 为 c8b7adab / modified=false。11,362 个独立输入路径、16,198 次引用校验通过，测试后再读全部输入，无漂移。

正式构建证据有 32 份 raw、1,844 份 WORK 与 680 份 archive，已逐一校验。作者 71 个 Go PASS 标记及退出 0 的回执被保留，本轮未重复此源码套件。作者 3 次失败（2 次 ACL 设置、1 次读取路径）仍完整保留。

独立新跑实际包的 **214/214** 个非 GUI 用例，native exit 0，fail/skip/cancel 均 0。固定源码中的 Main 模块与包字节一致；validator 从包绝对路径运行，其生产 spawn cwd 为包的 apps/desktop。原始回执记录 {len(real)} 个实际包 validator child，均 exit 0 且所有句柄关闭；另有隔离副本运行负例。原始 stdout 包含 {matched} 份携带新输入绑定的 child 输出。

安装 manifest 指向新包的 verifier 绝对路径，哈希正确。独立 Get-Acl 读取确认当前 SID owner、受保护 DACL、单条显式 FullControl ACE。Core/control 与 runtime-verifier 的 binary buildinfo 仍为 `a7ec7ebf`，Mu bundle 仍为 `8dfebe36`；迁移严格为 1–24。此包没有纳入 Native25/storage25/bridgecompat/Core17。

授权边界：本次只接受包的组成、来源、绑定和夹具测试。未启动正常 GUI，未访问真实产品 API/数据库/provider，未进行 CONFIRM，formal 增量 0。Root 后续应在原授权 data location 正常重开，验证已有保存状态 `c671505` / 新 Profile `mc3f932` 保留，不重复 coding CONFIRM。W05/Main24 及正式用例仍按原验收流程处理。

本轮 20 个负例临时目录已在检查绝对路径与唯一 alias 目标后清理；正式 raw 留存。测试与审查证据详见 FINAL-report.json、audit.json、fresh-package-cases.process.json、runtime-evidence-summary.json、fresh-acl.json、inputs.after.json、cleanup-result.json。审查读取截止 {post['at']}。
'''
(E/'REVIEW.md').write_text(md,encoding='utf-8',newline='\n')
files=[ref(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']
put('FINAL-manifest.json',dict(schema='researchos.independent-review-evidence-manifest/1',at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verdict=report['verdict'],count=len(files),members=files))
print(json.dumps({'verdict':report['verdict'],'report':ref(E/'FINAL-report.json'),'manifest':ref(E/'FINAL-manifest.json'),'review':ref(E/'REVIEW.md'),'count':len(files),'runtime':read(E/'runtime-evidence-summary.json')},ensure_ascii=False))
