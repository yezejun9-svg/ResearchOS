import pathlib,json,hashlib,subprocess,datetime,re
root=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees');ev=root/'attach-exact6-independent-evidence-20261013';work=root/'attach-exact6-independent-20261013'
def sha(b):return hashlib.sha256(b).hexdigest()
def get(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())}
census=get(ev/'resume-actual-compiler-census.json');build=census['work'];configs={};embedded={}
for command in census['commands']:
 a=command['argv']
 for flag in ['-importcfg','-embedcfg']:
  if flag not in a:continue
  p=pathlib.Path(a[a.index(flag)+1].replace('$WORK',build))
  if p.exists():
   configs[str(p)]=ref(p)
   if flag=='-embedcfg':
    for value in get(p).get('Files',{}).values():
     f=pathlib.Path(value)
     if f.exists():embedded[str(f)]=ref(f)
compiler=pathlib.Path(census['commands'][0]['argv'][0]);extra={'compiler':ref(compiler),'configurations':list(configs.values()),'embedded_files':list(embedded.values())}
(ev/'resume-compiler-config-embed.json').write_text(json.dumps(extra,indent=2),encoding='utf-8')
base='91218bdd3901bae94a2c1c90521a4d133c59026d';head='b955c8665281193d5cbf90a146f936c9212c7940'
def git(*a):return subprocess.check_output(['git','-C',str(work),*a])
def funcs(b):
 s=b.decode('utf-8');starts=list(re.finditer(r'^func ',s,re.M));out={}
 for i,m in enumerate(starts):
  sig=s[m.start():s.find('{',m.start())].strip();body=s[m.start():starts[i+1].start() if i+1<len(starts) else len(s)];out[sig]=body[:body.rfind('}')+1]
 return out
checks=[]
for p,exclude in [('internal/domain/client_protocol.go',['dispatch','handleWrite']),('internal/api/v2.go',['leaseTTL'])]:
 old=funcs(git('show',base+':'+p));new=funcs(git('show',head+':'+p))
 for sig,b in old.items():
  if any(re.search(r'\b'+name+r'\(',sig) for name in exclude):continue
  n=new.get(sig,'');checks.append({'path':p,'function':sig,'unchanged':b==n,'base_sha256':sha(b.encode()),'candidate_sha256':sha(n.encode())})
(ev/'resume-protected-production-functions.json').write_text(json.dumps(checks,indent=2),encoding='utf-8');assert all(c['unchanged'] for c in checks)
audit=get(ev/'resume-source-audit.json');assert audit['author_manifest_sha256']=='56224a50a2d57c8c75248b2e09417df9d5c18c72d31271a656bf5a68838001f0'
report={'schema':'researchos.attach-exact6-independent-review/1','status':'FINAL','verdict':'APPROVE_LIMITED_SCOPE','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reviewer':'codex:/root/attach_review_resume','model':{'model':'gpt-6-astra','reasoning_effort':'high','evidence':'orchestrator confirmed actual spawn_agent dispatch parameters, fork_turns=none; not inferred runtime internals'},'base':base,'candidate_commit':head,'candidate_tree':'00d44e133662227b115eb3b16bef3d4edcc35630','author_manifest_sha256':audit['author_manifest_sha256'],'scope':'Prospective synchronous attach-only six-file candidate; local native Windows domain/API/host tests and independent source review only. No Root integration or formal acceptance written.','findings':[],'P1_count':0,'P2_count':0,'scope_expansion_required':False,'source_checks':{'exact_six':True,'candidate_author_committed_bytes_match':True,'protected_test_and_helper_functions':34,'protected_production_functions':len(checks),'all_protected_unchanged':True,'diff_check_exit':0,'review_worktree_existing_untracked_file':'internal/domain/attach_independent_review_test.go retained; no tracked product source mutated; extra tests supplied by Go overlay'},'tests':[{'name':'original sparse independent attempt01','native_exit':1,'meaning':'Missing evaluation packages in sparse worktree; raw output retained, never reclassified PASS'},{'name':'original restored native run','native_exit':0,'top_level_pass':15,'meaning':'Actual -work -x compile and existing bounded synchronous/rollback/control/Windows HTTP suite'},{'name':'resume independent attempt01','native_exit':1,'meaning':'Reviewer fixture errors: stale revision 0 violates schema; synthetic historical ACK header field order violates private canonical representation. Retained. No product defect inferred.'},{'name':'resume independent attempt02','native_exit':0,'top_level_pass':3,'leaf_case_pass':15,'meaning':'Overlay-only corrected fixtures. 8 refusal cases, 3 active/historical Run cases, 4 HTTP current-project-authorization replay cases.'}],'authorization_conclusion':{'project_authority_model':'Global OWNER role plus current auth_grants project/task/run scope; no independent project role column.','cases':['COMPLETED + grant deleted','COMPLETED + grant narrowed to task-only','ACKNOWLEDGED + grant deleted','ACKNOWLEDGED + grant narrowed to task-only'],'result':'All four: global OWNER and token remain valid; HTTP 403 REJECTED/FORBIDDEN before Execute; writer tuple and immutable journal bytes unchanged. Authorized pre-revocation repeat is exact byte replay.','locations':['internal/api/v2.go:196 current project grant guard','internal/domain/client_protocol.go:728 lookup-before-dispatch unchanged','internal/domain/client_protocol_sessions.go:54 role plus grant model'],'inherited_behavior':'Execute identity replay remains before attach dispatch authorization by explicit frozen scope. Current HTTP project guard prevents revoked/narrowed project grant replay disclosure. No new defect found for tested public endpoint scenario. Direct in-process Execute is not newly qualified as an independent authorization boundary.'},'behavior_review':['New command ordinary same-client lease renewal COMPLETED; epoch/revision/watermark stable.','Expired foreign/null-lease acquisition checks local creation authority and settled authentic tasks/runs/effects/queues; epoch +1, revision +2, one handoff event.','Existing ACK is byte replay and remains ACK, never upgraded by a generic GET or new completion. handleRead and Execute byte-protected unchanged.','Refusals and injected faults retain writer state and roll back identity/event mutations as required.','Active canonical run permits ordinary same-client renewal but prevents foreign grant; detached historical Run blocks unsafe acquisition.','Mapped/unproven creation attribution, Device/non-owner, restore fences, malformed lease, invalid TTL and future cursor fail closed in bounded tests.'],'compiler_evidence':{'actual_compile_invocations':census['compile_command_count'],'actual_unique_go_input_files':census['unique_go_file_count'],'missing_input_files':len(census['missing']),'all_exact_six_observed_in_compile':all(census['exact_six_in_actual_compile'].values()),'compiler_configurations_hashed':len(configs),'embedded_files_hashed':len(embedded),'author_go_list_count_3854':'Potential dependency census only; not claimed actual compiler evidence.','limits':'Actual compile.exe Go inputs plus compiler/importcfg/embedcfg hashes; cache reuse and non-Go tool inputs are not asserted as fresh compiler runs.'},'failure_preservation':['independent-native-attempt01.*','resume-independent.*','original untracked reviewer test retained; overlay fixes sealed expectation to existing SESSION_ARCHIVED mapping','resume_audit.py initial locale decode failure retained as script; corrected audit02 explicitly UTF-8; no product changes'],'limitations':['Synthetic metadata/runtime ports in HTTP fixtures; this is not live provider or fresh current Desktop original-session qualification.','Historical ACK HTTP tests seed a valid SQL23 receipt; they do not manufacture the missing complete envelope of the original observed real ACK.','Full valid-foreign-writer async lifecycle, heartbeat scheduler, recovery reconciliation and safe retained follow-up queue support remain OPEN under existing source scope.','Original sealed-write SESSION_ARCHIVED mapping is inherited and unchanged; no scope expansion requested.','No Root Canon writes, no product package activation, no task acceptance.'],'formal_increment':0,'all22_42_remain_open':True,'next_authorized_integration_guidance':'Root may serially integrate exact6 against verified base while preserving independently owned session.list edits, then activate a clean package and obtain new current original Desktop-session evidence. This report does not itself perform those actions.'}
(ev/'FINAL-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
md='''# Core attach exact6 独立复核

结论：**APPROVE_LIMITED_SCOPE**。限定候选 `b955c8665281193d5cbf90a146f936c9212c7940`、tree `00d44e133662227b115eb3b16bef3d4edcc35630`，基线 `91218bdd3901bae94a2c1c90521a4d133c59026d`。P1=0，P2=0，不需要扩大修复范围。模型按主 Agent 确认的实际调度配置记录为 gpt-6-astra / high。

项目授权删除或收窄到 Task 后，global OWNER/token 仍有效时，旧 COMPLETED 与 ACK 的四种 HTTP 重放均返回 403 FORBIDDEN，writer 和不可变 journal 字节不变。有效授权下重复请求仍为原字节。Execute 提前 replay 是继承且受保护的实现；实际 HTTP 入口的当前 project grant guard 已拦截本次待决情景。直接进程内 Execute 没有因此获得独立权限边界资格。

独立原 native 运行 exit=0，15 个顶层测试通过。新增 overlay 复核 exit=0，3 个顶层、15 个叶子子例通过。首次稀疏缺 evaluation 的 exit=1、补测首轮夹具错误的 exit=1 全部保留；夹具错误分别为 revision=0 不符合 schema 和 ACK 私有头规范顺序不符，修复仅发生在新增证据文件。

六文件逐字节匹配作者 manifest、candidate 和 commit；34 个原测试/辅助函数及受保护生产函数保持不变，包含 control、rollback、session.list、Execute 和通用读取。实际 -work -x 记录了 367 次 compile.exe、2363 个唯一 Go 输入，缺失 0，六文件均出现在真实编译命令中。author 的 go list 3854 仅为潜在依赖清单。compiler、importcfg、embedcfg 及嵌入文件另有 hash 清单。

新命令同步 attach 完成返回 COMPLETED；普通同 client 续约不增加 epoch/revision/event；过期异 client 授权为 epoch+1、revision+2、一个 handoff；旧 ACK 永久保持原响应。失败回滚、未结算历史 Run、active Run 下同 writer 续约、恢复 fence 等边界已复核。

此结论只授予有限 source/local-native/fixture-HTTP 复核通过。当前原 Desktop 会话、新干净包激活、live provider、完整 B22 和全部 22/42 正式接受均不由本报告完成。formal_increment=0，all22_42_remain_open=true。Root 可以依原授权串行整合精确六文件并继续真实主流程。本复核没有修改 Root Canon 或接受任务。

关键证据：`resume-source-audit.json`、`resume-protected-production-functions.json`、`resume-actual-compiler-census.json`、`resume-compiler-config-embed.json`、`independent-native.*`、`resume-attempt02-independent.*`。全部原始命令、环境、native exit 和新旧失败均纳入 FINAL-manifest.json。
'''
(ev/'FINAL-report.md').write_text(md,encoding='utf-8')
manifest={'schema':'researchos.attach-exact6-independent-manifest/1','report':ref(ev/'FINAL-report.json'),'candidate_commit':head,'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[ref(p) for p in sorted(ev.iterdir()) if p.is_file() and p.name not in ['FINAL-manifest.json','FINAL-manifest.sha256']]}
(ev/'FINAL-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');(ev/'FINAL-manifest.sha256').write_text(sha((ev/'FINAL-manifest.json').read_bytes())+'  FINAL-manifest.json\n',encoding='ascii')
print(json.dumps({'report':ref(ev/'FINAL-report.json'),'manifest':ref(ev/'FINAL-manifest.json'),'protected_production_functions':len(checks),'embedded_file_count':len(embedded),'configuration_count':len(configs)},indent=2))
