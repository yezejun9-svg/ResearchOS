import pathlib,json,hashlib,subprocess,datetime
E=pathlib.Path(__file__).parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');S=R/'.local/worktrees/schema24-to25-native-20261014';A=R/'execution/v2.4/receipts/W17/W17-03/schema24_to25_source_codex/20261014-current-chat/revision01';G=R/'.local/tools/go1.27.1/go';read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda b:hashlib.sha256(b).hexdigest();pin=lambda p:{'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
inputs=read(E/'inputs.before.json')
for x in inputs:assert sha(pathlib.Path(x['path']).read_bytes())==x['sha256'] and pathlib.Path(x['path']).stat().st_size==x['bytes']
def git(*a):return subprocess.check_output(['git','-C',str(S),*a])
assert git('status','--porcelain')==b'';assert git('rev-parse','HEAD').decode().strip()=='f80955594bdd0373ae1c961cd02ab6be96f2c196';assert git('rev-parse','HEAD^{tree}').decode().strip()=='5bce20214223e8292f16a117a83407f52b4bca4a'
(E/'git-status.final.raw').write_bytes(git('status','--short'))
def census(path):
 es=[json.loads(x) for x in path.read_text(encoding='utf8').splitlines() if x.strip().startswith('{')];ps={(x['Package'],x['Test']) for x in es if x.get('Action')=='pass' and 'Test' in x};return {'top':sum('/' not in t for _,t in ps),'leaves':sum(not any(q==p and n.startswith(t+'/') for q,n in ps) for p,t in ps),'fail':[e for e in es if e.get('Action')=='fail'],'skip':[e for e in es if e.get('Action')=='skip']}
fresh=census(E/'fresh-regression.stdout.raw');assert (fresh['top'],fresh['leaves'])==(66,249) and not fresh['fail'] and len(fresh['skip'])==1 and 'Test' not in fresh['skip'][0]
minimal=census(E/'minimal-env-test.stdout.raw');assert minimal['top']==1 and not minimal['fail'] and not minimal['skip'];minimalob=read(E/'minimal-env-child-observation.json');assert minimalob['environment_names']==['SystemRoot','WINDIR'];assert minimalob['ambient_temp_reported_without_writing'].lower()=='c:\\windows';assert minimalob['explicit_parent'].lower().startswith(str(E/'minimal-env-temp').lower());assert [x['existing_destination'] for x in minimalob['runs']]==[False,True] and all(x['remaining_stages']==0 for x in minimalob['runs'])
author_counts={n:census(A/n/'stdout.jsonl') for n in ['31-signed-stage-boundary-fixed','32-old-and-pause-regressions','37-revision-public-cli-handoff']};assert [(x['top'],x['leaves']) for x in author_counts.values()]==[(5,29),(66,249),(1,1)]
oldledger=read(A.parent/'ledger.json');ledger=read(A/'ledger.json');assert len(ledger['attempts'])==37 and ledger['attempts'][:29]==oldledger['attempts'];assert sum(x['exit']!=0 for x in ledger['attempts'])==4 and sum(x['exit']!=0 for x in oldledger['attempts'])==3
cp=read(A/'target25-r4-build-inputs/compiler-inputs.json');names={str(pathlib.Path(x['path']).resolve()).lower() for x in cp['inputs']};raw=(A/'target25-r4-build-inputs/go-list.stdout.raw').read_text(encoding='utf8');dec=json.JSONDecoder();offset=0;pkgs=[]
while raw[offset:].strip():offset+=len(raw[offset:])-len(raw[offset:].lstrip());p,offset=dec.raw_decode(raw,offset);pkgs.append(p)
selected=set()
for p in pkgs:
 for key in ['GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles']:
  for name in p.get(key,[]):selected.add(str((pathlib.Path(p['Dir'])/name).resolve()).lower())
assert selected<=names
versions=[]
for p in read(A/'target25-r4-build-inputs/programs.json'):
 argv=[str(G/'bin/go.exe'),'version','-m',p['path']];proc=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE);out=proc.stdout.decode('utf8');assert proc.returncode==0 and 'go1.27.1' in out and 'vcs.modified=false' in out and 'vcs.revision=f80955594bdd0373ae1c961cd02ab6be96f2c196' in out
 (E/(p['role']+'.go-version-m.stdout.raw')).write_bytes(proc.stdout);(E/(p['role']+'.go-version-m.stderr.raw')).write_bytes(proc.stderr);versions.append({'argv':argv,'native_exit':proc.returncode,'program':p})
public=A/'public-cli-handoff04';case=read(public/'05-case.result.json');assert case['status']=='PUBLIC_CLI_REHEARSAL_ONLY_NATIVE_NOT_RUN' and case['original_unchanged'] and case['before_rows_sha256']==case['after_rows_sha256'];assert read(public/'before.rows.json')==read(public/'after-original.rows.json')
observations={}
for n in ['00-source-backup','00-rehearsal']:
 j=read(public/n/'invocation.json');r=j['Result'];c=r['job_cleanup'];assert r['actual_exit']==0 and not r['timed_out'] and r['error'] is None and c['active_processes_last_observed']==0 and c['job_idle_confirmed'] and c['primary_exit_confirmed'] and c['handles_closed'] and not c['errors'];assert j['ActualLifetimeClosed'] and not j['NativeAuthorityAcceptance'];observations[n]=j
audit={'status':'SOURCE_ACCEPTED_P2_CLOSED_NATIVE_TRIAL_READY','closed_finding':'P2-NATIVE-TEMP-001','input_files_verified':len(inputs),'revision_scope':6,'combined_scope':22,'other16_identical_to_reviewed_base':True,'readonly_guards_unchanged':True,'original274_author_artifacts_unchanged':True,'fresh_tests':fresh,'minimal_environment_test':minimal,'minimal_environment_observation':minimalob,'author_counts':author_counts,'author_attempts':37,'preserved_failures':4,'compiler_coverage':{'packages':len(pkgs),'selected_files':len(selected),'pins':len(names),'missing':[]},'programs':versions,'public_case':case,'public_observations':observations,'native_run':False,'signing':False,'formal_increment':0,'source_read_finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(E/'independent-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for name in ['fixture-temp','minimal-env-temp']:
 temp=(E/name).resolve();assert temp.parent==E.resolve();temp.rmdir()
report='''# Native25 subset6 revision01 独立复查

结论：**SOURCE_ACCEPTED_P2_CLOSED_NATIVE_TRIAL_READY**。原 `P2-NATIVE-TEMP-001` 已关闭，没有新增 findings。当前 exact22 candidate 已满足开展后续 Root 隔离 Native 试验的源码先决条件；使用本修订 r4 程序和新 case，仍由 Root 按原流程审查具体 release/grant 并签名。本轮没有执行 Native 迁移或签名，formal increment = 0。

## 范围、冻结与继承

- Worktree `D:/作品集/ResearchOS/research-os/.local/worktrees/schema24-to25-native-20261014`；HEAD `f80955594bdd0373ae1c961cd02ab6be96f2c196`；tree `5bce20214223e8292f16a117a83407f52b4bca4a`；修订base `1b5ec5d049db7811f6e0d8b143659ea5e2f0836b`。
- CP476 scope SHA256 `e1447f6b0dd535e16d125adab931a871194c764989d0cc037f50a951a59fcf23`；作者报告 SHA256 `45f2d6a8e931c8c2c2b03ba9d3568ed3af596a65de2dbfec6c0242562d9fd1e1`；manifest SHA256 `678eb7697a703cae67a65275507c507ca73c7d07647bfece7e825be7d2bf2686`，109项新证据全部核验。
- 相对原审查candidate仅subset6变化，合并相对原始base仍exact22。其余16份源码与reviewer原snapshot相同，原只读依赖与父commit相同。原274份作者artifact、旧报告、manifest及reviewer原finding完整保留，未重写为通过。
- 本次2723个唯一输入pin在结束再次核验无漂移；Git clean，diff --check通过。沿用原审查中不受本次变更影响的生产链、token、purpose隔离和harness判断。

## P2关闭依据

新 `pauseMigrationTemplate` 显式接收该调用的 options 和 `filepath.Dir(Destination)`；普通public handoff与Native leaf都使用各自同一options对象的Destination。Native调用仍位于opaque token绑定、签名OptionsSHA256、canonical options、inventory和program pins验证之后。未新增可由调用方单独指定的temp授权字段，也未更改signed options字节定义。

新pause-only helper先验证固定plan、父目录与Destination对应、绝对路径、query/fragment/NUL拒绝、native canonical resolution、存在的目录父级和已有Destination必须为目录；并检查stage parent与数据库目录、key目录、snapshot和source/target release root在两个方向都不重叠。共享路径入口在规范化前检查，防止抹去junction证据；创建前再次检查。创建调用现在明确为 `os.MkdirTemp(parent, ...)`，不查询TEMP/TMP/TMPDIR，也不创建缺失parent或退回系统临时目录。

独立补充的**真实子进程fixture**只继承SystemRoot/WINDIR，TEMP/TMP/TMPDIR/USERPROFILE等均不存在。子进程报告 `os.TempDir()` 仍为 `C:\\Windows`，但完整模板构建在新Destination及已有Destination两种场景都成功使用显式D盘parent，生成四项schema digest并清理临时stage。这直接复现了原Native child的环境限制而不读取/签发Native token：属于unsigned template fixture，不是Root→control Native authority执行。本轮没有在C Windows写入。

现有 `.researchos-backup-stage-` prefix保持与受限backupDiscard一致。作者capture30曾换prefix造成stage未清理，该失败保留；现修订恢复prefix，独立完整模板运行和fresh回归均验证清理成功。旧23→24环境、namespace、authority、helper和signed options未修改。

## 新证据独立核验

- 六包fresh回归：**66 top-level / 249 leaf，native exit0**。没有测试级skip/fail；enrollment无测试是唯一package-level skip。覆盖missing/empty/hostile TEMP、18项不合法path/binding/overlap、4项实际Windows junction、public handoff以及旧23→24回归。
- 独立最小环境子进程fixture：**1 top-level，native exit0**，新/已有Destination两次完整模板均pass；没有签名、DPAPI或原库访问。源码AST wiring检查只作为source证据，未冒充Native调用。
- 重新从作者raw JSON推导capture31=5top/29leaf、capture32=66top/249leaf、capture37=1top/1leaf。revision ledger前29项与原ledger逐项相同；总37次attempt/4失败保留。
- r4 compiler原始go-list独立推导363 packages / 2285 selected source/embed files，全部被2311 input pins覆盖，无遗漏。四个r4 executable独立 `go version -m` 均Go1.27.1、精确新HEAD、vcs.modified=false；原source24 binary保持原pin。
- 作者实际 old24 producer→r4 public CLI链：两进程actual exit0、job active=0、primary exited、handles closed、无cleanup错误。原typed row before/after JSON独立相等，case仍明确为 `PUBLIC_CLI_REHEARSAL_ONLY_NATIVE_NOT_RUN`；未将此证据当Native原库迁移接受。本轮为核对现有raw，没有重复公开CLI执行。

## 后续 Root 隔离 Native 试验条件

采用 `public-handoff04.config.json` 与 `target25-r4-build-inputs/programs.json` 的新pins，不再使用r3。每个case的Destination parent必须为独立、已存在、canonical、与protected inputs不重叠的D盘目录，并包含在待审signed options中；Root/control仍按原harness同目录及fresh namespace约束。继续逐项检查实际release/grant payload、hash、identity、expiry、nonce和负例预期，不因本次source接受省略具体payload审查。

Native positive/replay、拒绝路径、原产品迁移、Main整合和最终安装包都尚未由本卡验证。本轮只写revision01独立证据；Source/Main/原DB/GUI/原产品进程/真实model均未动。测试临时文件已自动清理并移除空目录；原审查及失败历史保持不变。
'''
(E/'REVIEW.md').write_text(report,encoding='utf8')
r={'schema':'researchos.native25-subset6-independent-recheck/1','status':audit['status'],'closed_findings':['P2-NATIVE-TEMP-001'],'new_findings':[],'head':'f80955594bdd0373ae1c961cd02ab6be96f2c196','tree':'5bce20214223e8292f16a117a83407f52b4bca4a','revision_scope':6,'combined_scope':22,'fresh_tests':{'top':66,'leaf':249,'native_exit':0},'minimal_environment_fixture':{'top':1,'native_exit':0,'ambient_temp':'C:\\Windows','actual_stage':'explicit Destination parent in D'},'root_isolated_native_trial_source_prerequisites_met':True,'native_execution':'NOT_RUN','signing':'NOT_RUN','formal_increment':0,'source_read_finished_at':audit['source_read_finished_at'],'review_sha256':sha((E/'REVIEW.md').read_bytes())}
(E/'FINAL-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8');members=[pin(p) for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json'];(E/'FINAL-manifest.json').write_text(json.dumps({'schema':'researchos.independent-source-recheck-artifacts.v1','artifacts':members},ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'status':r['status'],'review_sha256':sha((E/'REVIEW.md').read_bytes()),'report_sha256':sha((E/'FINAL-report.json').read_bytes()),'manifest_sha256':sha((E/'FINAL-manifest.json').read_bytes()),'members':len(members),'source_read_finished_at':r['source_read_finished_at']},ensure_ascii=True))
