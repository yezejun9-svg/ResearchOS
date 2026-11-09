import pathlib,json,subprocess,hashlib,datetime
E=pathlib.Path(__file__).parent; A=E.parents[1]/'schema24_to25_source_codex'/'20261014-current-chat'; S=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014')
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=read(E/'unique-input-pins.before.json')
for x in before:
 p=pathlib.Path(x['path']);assert sha(p)==x['sha256'] and p.stat().st_size==x['bytes'],str(p)
def git(*a):return subprocess.check_output(['git','-C',str(S),*a])
assert git('rev-parse','HEAD').decode().strip()=='1b5ec5d049db7811f6e0d8b143659ea5e2f0836b'
assert git('rev-parse','HEAD^{tree}').decode().strip()=='3a7d5085a5389ea89ceae8dab637d1fb4f0f9b43'
assert git('status','--porcelain')==b''
(E/'git-status.after.raw').write_bytes(git('status','--short'))
# Independent derivation from author raw event streams; do not rewrite the author's historical ledger.
def census(p):
 events=[json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip().startswith('{')]; passed={(e['Package'],e['Test']) for e in events if e.get('Action')=='pass' and 'Test' in e}
 return {'top':sum('/' not in n for _,n in passed),'leaf':sum(not any(q==p and t.startswith(n+'/') for q,t in passed) for p,n in passed),'fail':sum(e.get('Action')=='fail' for e in events)}
counts={name:census(A/name/'stdout.jsonl') for name in ['13-final-source-regressions','24-private-open-path-boundary','29-final-public-cli-handoff']}
assert [(x['top'],x['leaf'],x['fail']) for x in counts.values()]==[(60,212,0),(2,9,0),(1,1,0)]
captures=sorted(p for p in A.iterdir() if p.is_dir() and len(p.name)>2 and p.name[:2].isdigit() and p.name[2]=='-');assert len(captures)==29
failed=[]
for p in captures:
 events=[json.loads(x) for x in (p/'stdout.jsonl').read_text(encoding='utf8').splitlines() if x.strip().startswith('{')]
 if any(e.get('Action')=='fail' for e in events): failed.append(p.name)
assert len(failed)==3,failed
pub=A/'public-cli-handoff03';b=read(pub/'before.rows.json');a=read(pub/'after-original.rows.json');assert b==a
observations={}
for n in ['00-source-backup','00-rehearsal']:
 d=read(pub/n/'invocation.json');r=d['Result'];j=r['job_cleanup'];assert r['actual_exit']==0 and not r['timed_out'] and r['error'] is None and j['active_processes_last_observed']==0 and j['job_idle_confirmed'] and j['primary_exit_confirmed'] and j['handles_closed'] and not j['errors'] and d['ActualLifetimeClosed'] and not d['NativeAuthorityAcceptance']
 observations[n]=d
for rel in ['internal/domain/backup_prepared_abandonment_upgrade.go','internal/recoveryauthority/native_windows.go']:
 p=E/'dependency-snapshot'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((S/rel).read_bytes())
goroot=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/src/os/file_windows.go')
(E/'go1.27.1-os-file_windows.go').write_bytes(goroot.read_bytes())
audit={'input_files_rechecked':len(before),'input_drift':[],'git_clean':True,'author_census':counts,'author_capture_count':len(captures),'preserved_failed_captures':failed,'public_handoff_original_typed_rows_unchanged':True,'public_process_observations':observations,'source_read_finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(E/'final-integrity-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
temp=(E/'fixture-temp').resolve();assert temp.parent==E.resolve();temp.rmdir()
report='''# schema24→25 Native 独立源码审查

结论：**FINDINGS / NEEDS_REVISION_BEFORE_NATIVE**。原 candidate 有 1 项 P2 必须修正；本轮没有发现第二项需要阻止后续隔离 Native 验证的问题。此结论仅绑定下列冻结源码，不对修订版或 Native 执行作接受判断。formal increment = 0。

## 冻结输入与独立性

- Worktree: `D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014`。
- Base `60f8c81a7529081eb51d525ab913d63102148a46`；HEAD `1b5ec5d049db7811f6e0d8b143659ea5e2f0836b`；tree `3a7d5085a5389ea89ceae8dab637d1fb4f0f9b43`，exact 22 paths，审查前后 clean，diff --check 通过。
- 作者 SOURCE_REPORT SHA256 `91570238b80db2037d15b6b33862ffc7f39d345179ce6443e34ea742f688f4dc`；manifest SHA256 `00ff8811feefb3ef2c515470a4b6ed4a6438dc540594d0a743ebba7e265717ff`。
- 独立核验 274 个作者证据成员、4891 个 pin occurrences / 2881 个唯一文件；审查结束再次核对全部 2881 个文件，无漂移。22 份冻结源码同时与 Git blob、作者 snapshot、live bytes 一致。
- reviewer 仅向本审查证据目录写入；没有修改 Source、Main、原产品数据库或原进程，没有读取 issuer secret，没有签名，没有运行 Native harness 或真实迁移。

## P2：新 Native 分支的模板库临时目录逃出显式 D 盘隔离范围

定位：`internal/domain/backup_pause_migration.go:217`，`pauseMigrationTemplate` 的 `os.MkdirTemp("", ".researchos-backup-stage-")`；关联 `internal/recoveryauthority/migration_windows.go:83` 和 `internal/domain/backup_pause_migration_windows.go:150`。

实际 Root 启动 control 子进程时，`child.Env` 仅保留 SystemRoot、WINDIR 与 private bootstrap，不保留 harness 的 TEMP/TMP。新 private schema24→25 路径会调用 `pauseMigrationTemplate`，空目录参数转入 Go 1.27.1 的 Windows tempDir/GetTempPath2W。使用同样的环境（仅省略不会影响临时路径的 bootstrap 变量）的独立只读 API 探针，GetTempPathW 与 GetTempPath2W 均返回 `C:\\Windows\\`。因此当前 Native 正例会尝试在未绑定的 C 盘系统目录创建模板库，而不是已声明的 D 盘隔离目录。普通 public handoff 和现有 fixture tests 继承 TEMP/TMP，所以它们通过不能覆盖该生产链差异。探针没有创建文件，也没有测试目录写权限；本报告不声称已观察到 AccessDenied 或 Native 运行失败。

建议在新 pause 分支显式传入已 canonicalize、已由 signed options 绑定且通过路径互斥校验的 staging parent，例如 Destination 的 parent。最小源码影响为 `backup_pause_migration.go`、两个调用点 `backup_pause_handoff.go` / `backup_pause_migration_windows.go` 及相应 scoped tests。不要以扩展旧23→24 child environment 或接受任意外部环境变量代替这个修复。回归应证明在 TEMP/TMP 缺失或指向其他位置时，新模板始终位于显式授权目录，且旧23→24行为保持原样。修订后重新 freeze、重建 target binaries 并审查，再由 Root 执行已授权的隔离 Native 用例。

## 已核对的生产链与证据

- `apps/control` 的新 private 参数分支在普通启动前截获，拒绝 caller 参数、相对路径、query/fragment、root/database 绑定不一致；只通过 opaque Native token 调用新 schema24→25 leaf。
- 新 plan/purpose/schema/argument/Root operation/grant filename/nonce namespace 与旧23→24隔离；共享 trusted descriptors 不开放任意 SQL。旧签名字节及旧 purpose 仍被现有回归覆盖。
- Root 校验当前 release、issuer、native image/file identities、pins 和一次性 nonce；leaf 再检查 signed options、三程序（真实旧 producer、新 control、新 rehearsal backup）、完整 encrypted backup、raw producer observations、inventory、rehearsal 与固定 SQL25。公开 handoff 只提供可核验材料，不授予 Native 权限。
- 当前 Owner token 和直接 Root Owner 角色在数据库事务中重查。source lease、exclusive open、resourceWriteLock、typed row snapshot、固定25 SQL、完整 migration history、旧表列/行不变以及新增三表为空均有 fail-closed 检查。row hash 区分 NULL、int64、float64 bits、TEXT、BLOB；不经过 JSON 数字转换。Commit 不确定时保守消耗 token，保留 durable intent，不自动重试。
- public handoff 的真实旧 producer 来自 commit `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`，并非 target binary 冒充。独立 `go version -m` 检查全部五个程序：锁定 Go1.27.1，目标四程序精确 HEAD，全部 `vcs.modified=false`。
- compiler input coverage 独立从原始 concatenated go-list JSON 推导：source24 350 packages / 2229 selected files，全被2255 pins覆盖；target25-r3 363 packages / 2285 selected files，全被2311 pins覆盖，无缺项。toolchain/module locks 在独立 hash 核验内。
- 作者 final public CLI handoff 两个进程均 actual_exit 0、未超时、exclusive job drained=0、primary exited、handles closed。before/after original typed rows JSON 独立相等；receipt 明确为 `PUBLIC_CLI_REHEARSAL_ONLY_NATIVE_NOT_RUN`。这些已保存的作者观察经过独立核对，本轮未重跑该 CLI 链。
- Native harness 源码覆盖 positive-replay、missing-native-channel、wrong-purpose、mismatched-database、release-pin-mismatch、expired-grant、missing-dynamic-pin、wrong-owner、lease-occupied。签名由 Root 外部执行，harness 仅等待 exact payload/signed hashes approval；wrong-purpose 故意用旧 grant kind，missing-dynamic-pin 保留 signer 结构有效但删 leaf 必需 pin。负例要求版本24与全部 typed rows 不变，正例要求版本25与业务行不变、空新表、replay拒绝。源码审查不等于这些 Native 用例实际通过；inner Root child job 身份没有被额外观察的事实应继续保留。

## 独立执行与计数

对冻结源码执行锁定 Go1.27.1 的六包 scoped regression，`-mod=readonly -count=1`，Native harness 配置未设置，网络 modules 禁用，显式 D 盘 TEMP/TMP/GOTMPDIR。native exit 0；61 top-level / 220 leaf cases 通过，无测试级 skip/fail；enrollment 包无测试，单独 package-level skip。原始 stdout JSONL、stderr、完整 argv/cwd/environment/耗时均保留。

作者原始计数另外重新推导：capture13=60 top/212 leaf；capture24=2 top/9 leaf；capture29=1 top/1 leaf。29 次 capture 中的3次历史失败保留，未重置、未覆盖。审查辅助查询曾有一次错误文件名和一次 Windows rg glob 无匹配，均未更改输入、未计作产品失败。

## 停读与后续边界

本报告冻结后，reviewer 停止读取此 live worktree，后续 Root 可另行授权作者修订；既有 snapshot、raw evidence、作者失败记录和本次 finding 全部保留。需要修正 P2 后重新提供 exact source/program pins；尚未进行 Native positive/negative/replay、原产品迁移、Main integration、正式用例接受。不能将本轮 source/fixture/public handoff 结果转换为这些接受状态。
'''
(E/'REVIEW.md').write_text(report,encoding='utf8')
r={'verdict':'FINDINGS_NEEDS_REVISION_BEFORE_NATIVE','head':'1b5ec5d049db7811f6e0d8b143659ea5e2f0836b','tree':'3a7d5085a5389ea89ceae8dab637d1fb4f0f9b43','scope_count':22,'findings':[{'id':'P2-NATIVE-TEMP-001','priority':2,'file':'internal/domain/backup_pause_migration.go','line':217,'evidence':'native-inner-temp-observation.json'}],'fresh_tests':read(E/'additional-integrity-audit.json')['fresh_tests'],'native_executed':False,'signing_performed':False,'formal_increment':0,'source_read_finished_at':audit['source_read_finished_at'],'review_sha256':sha(E/'REVIEW.md')}
(E/'FINAL-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
members=[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json']
(E/'FINAL-manifest.json').write_text(json.dumps({'schema':'researchos.independent-source-review-artifacts.v1','artifacts':members},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'verdict':r['verdict'],'report_sha256':sha(E/'REVIEW.md'),'final_report_sha256':sha(E/'FINAL-report.json'),'manifest_sha256':sha(E/'FINAL-manifest.json'),'members':len(members),'source_read_finished_at':audit['source_read_finished_at']},ensure_ascii=True))
