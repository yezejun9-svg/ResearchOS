import hashlib,json,pathlib,sys
E=pathlib.Path(__file__).parent
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def put(name,v):
    with (E/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
checked=json.loads((E/'NATIVE-PROOF-INDEPENDENT-CHECK.json').read_bytes())
assert checked['verdict']=='OWNED_NATIVE_SMOKE_EVIDENCE_REVIEW_PASS_LIMITED' and checked['blocking_findings']==0
put('REVIEW-DIAGNOSTICS.json',{'new_review_failures':0,'new_review_nonzero_native_exits':0,'review_invocations':[{'script':'capture_native_inputs.py','native_exit':0,'observed_tool_chunk':'dbe903'},{'script':'verify_native_proof.py','native_exit':0,'observed_tool_chunk':'2d3c44'}],'bootstrap_read':'Scope/proof/outer-result read in tool chunk d407bf preceded local capture recipe and is explicitly not claimed as pre-recorded. Exact bytes were then captured and verified.','previous_source_review_diagnostics':'Retained unchanged under sibling complete-tree seal 2981911af85ea4163389592041a9474f0ed5ed8e027ba5ac131e3912560b939c','management_diagnostic':'Native report records 68 diagnostic bytes, SHA ddaa342ab313939b18d1ba189d6aa7731b4fc4b9c05b9d98a81db81738749331, truncated=false; this review does not reinterpret an unavailable diagnostic body. Native stderr is empty.','reviewer_native_reruns':0,'reviewer_process_queries':0,'original_resource_direct_reads':0,'formal_increment':0})
report='''# CP553 owned Desktop native smoke — independent evidence review

**结论：OWNED_NATIVE_SMOKE_EVIDENCE_REVIEW_PASS_LIMITED。** 本次全新自有状态目录内的 Desktop 启动、真实 React/native host.status、同一自有 Core 安全退出证据通过复核；无阻断发现，可供 CP554 封存。

复核绑定 scope SHA-256 `328aeca61c34d84d2a8931181c4d08d0a885d1e61145dc733d1bc3ae71f802bf`、候选 `ecc28dd3c91a0f68dcddb41b53325aa7f0e81419`、bundle manifest `e1d61b68d12c61e2dda341df3541d2b4b541b9c2331af5da26ca56dff759b620`，以及 native-proof `23111efd8606c7d6380497c72a59cf119b89ed0cc205de42584c5f22babf685b`。18 份原始执行回执与 scope 的10个绑定文件均核对 SHA/bytes，包含实际 Node、Electron、Core、verifier、launcher、runner 与前序独立 source/build seal。

原始 stdout 严格 UTF-8 解码正常，报告顺序为 ready_to_show、shutdown_confirmed、NATIVE_SMOKE_CONFIRMED。Desktop PID 84648，management READY、Host UP，React bridge/root、标题“项目入口”、10个导航项存在，native_probe.ok=true、protocol_status=COMPLETED。Core PID 12144、creation `1792921594448754600`、image SHA `3e45078c3108418f90092b02291ff79c3dca100afcec5bc4a95f085394bf185c`、Host ID `host-b86c7d65bcf4` 在 ready、shutdown 与 launcher final 中完全一致；image hash 等于 scope 绑定的实际 Core 二进制。

launcher、外层执行及 exact-PID 后查均 exit 0；运行17.32405秒，timed_out=false，raw_capture_status=SEALED_AFTER_LAUNCHER_EXIT，未把超时未封存快照当成成功证据。退出报告明确 process_exit_confirmed=true；留存后查命令仅查询84648、12144，原始结果两者均不存在。独立复核未重新查询进程。

执行前后保全 JSON 完全相等：Main `7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e`、C57 frozen `03aa4d687dfaa541d9b18d4c766805307a537d1d`、20条已有dirty、9项protected、33项old assets、3项new assets及48个verified refs。finally 的 originals.after 已产生，保全错误文件不存在；外层退出0包含 finally 成功。这里核对的是已记录的保全证据，没有扩大读取原数据、数据库或凭据。

本轮仅只读核对证据及精确scope绑定文件，并在本独立 native-proof 目录写复核产物；未重跑GUI/Core、未改source/state/Main、未进行进程控制。新复核失败或非零退出为0，前序所有诊断继续保留。管理报告68字节诊断的hash已记录，未取得其正文，因此不为其内容添加解释。

本结论只覆盖这次新状态目录的 owned native smoke。它不证明 C57 原实例恢复、disarm/FullRestart、安装器、provider/model调用、W13/W20全项或任何正式v2.4验收；formal_increment=0。独立管理员会话和原实例资源状态不由本证据确认。
'''
with (E/'NATIVE-PROOF-REVIEW.md').open('x',encoding='utf-8',newline='\n') as f:f.write(report)
put('003-seal.recipe.json',{'argv':[sys.executable,'-B','-Xutf8',str(E/'seal_native_review.py')],'mode':'SEAL_EXISTING_EVIDENCE_NO_NATIVE_RERUN','writes':str(E)})
rows=[]
for p in sorted(E.rglob('*')):
    if p.is_file() and p.name not in ['NATIVE-PROOF-REVIEW-MANIFEST.json','NATIVE-PROOF-REVIEW-SEAL.json']:
        rows.append({'path':p.relative_to(E).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
put('NATIVE-PROOF-REVIEW-MANIFEST.json',{'schema':'researchos.owned-native-desktop-independent-review-manifest.v1','root':str(E),'source_scope_sha256':checked['scope_sha256'],'source_native_proof_sha256':checked['proof_sha256'],'files':rows})
for row in rows:assert sha(E/row['path'])==row['sha256']
seal={'schema':'researchos.owned-native-desktop-independent-review-seal.v1','verdict':checked['verdict'],'candidate_commit':checked['candidate_commit'],'bundle_manifest_sha256':checked['bundle_manifest_sha256'],'scope_sha256':checked['scope_sha256'],'native_proof_sha256':checked['proof_sha256'],'report_sha256':sha(E/'NATIVE-PROOF-REVIEW.md'),'independent_check_sha256':sha(E/'NATIVE-PROOF-INDEPENDENT-CHECK.json'),'diagnostics_sha256':sha(E/'REVIEW-DIAGNOSTICS.json'),'review_manifest_sha256':sha(E/'NATIVE-PROOF-REVIEW-MANIFEST.json'),'review_file_count':len(rows),'blocking_findings':0,'root_native_smoke_runs_represented':1,'reviewer_native_reruns':0,'formal_increment':0,'C57_recovery_or_acceptance':False,'installer_acceptance':False}
put('NATIVE-PROOF-REVIEW-SEAL.json',seal)
print(json.dumps({'verdict':seal['verdict'],'report_sha256':seal['report_sha256'],'manifest_sha256':seal['review_manifest_sha256'],'seal_sha256':sha(E/'NATIVE-PROOF-REVIEW-SEAL.json'),'file_count':len(rows),'formal_increment':0}))
