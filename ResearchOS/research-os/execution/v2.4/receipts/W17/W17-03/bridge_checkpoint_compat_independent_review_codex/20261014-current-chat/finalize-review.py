import pathlib,json,hashlib,subprocess,datetime,base64,re
E=pathlib.Path(__file__).parent;S=pathlib.Path('D:/作品集/ResearchOS/research-os/.local/worktrees/bridge-checkpoint-compat-20261014');read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda b:hashlib.sha256(b).hexdigest();digest=lambda b:'sha256:'+sha(b)
pins=read(E/'inputs.before.json')
for x in pins:
 p=pathlib.Path(x['path']);assert sha(p.read_bytes())==x['sha256'] and p.stat().st_size==x['bytes'],str(p)
def git(*a):return subprocess.check_output(['git','-C',str(S),*a])
assert git('rev-parse','HEAD').decode().strip()=='0f9a870aed72785297a9999396fc8c760b296e13';assert git('rev-parse','HEAD^{tree}').decode().strip()=='fa071c9be7e39628c0b86ad43f77d5c50be63c7c';assert git('status','--porcelain')==b''
(E/'git-status.final.raw').write_bytes(git('status','--short'))
def census(name):
 es=[json.loads(x) for x in (E/(name+'.stdout.raw')).read_text(encoding='utf8').splitlines() if x.strip().startswith('{')];ps={(e['Package'],e['Test']) for e in es if e.get('Action')=='pass' and 'Test' in e};fail=[e for e in es if e.get('Action')=='fail'];skip=[e for e in es if e.get('Action')=='skip'];assert not fail and not skip
 return {'top':sum('/' not in t for _,t in ps),'subtest':sum('/' in t for _,t in ps),'leaves':sum(not any(q==p and n.startswith(t+'/') for q,n in ps) for p,t in ps),'native_exit':read(E/(name+'.process.json'))['native_exit'],'log_outputs':[e['Output'] for e in es if 'Output' in e and ('NATIVE_' in e['Output'] or 'RUNTIME_CHECKPOINT_' in e['Output'] or 'RUNTIME_CONTROL_' in e['Output'])]}
counts={n:census(n) for n in ['fresh-runtime','fresh-legacy-core','fresh-supplement']};assert all(x['native_exit']==0 for x in counts.values())
observations={}
for name in ['pause','resume','ordinary-unnegotiated-mu']:
 d=E/'native-capture'/name;j=read(d/'bridge.json');receipt=j['sandbox_receipt'];request=read(d/'input/request.json');frames=[json.loads(x) for x in (d/'stdout.raw').read_bytes().splitlines() if x]
 assert digest((d/'stdout.raw').read_bytes())==j['stdout_hash'] and digest((d/'stderr.raw').read_bytes())==j['stderr_hash'] and digest((d/'input/request.json').read_bytes())==j['input_hash']
 assert base64.b64decode(receipt['stdout'])==(d/'stdout.raw').read_bytes() and base64.b64decode(receipt['stderr'])==(d/'stderr.raw').read_bytes()
 assert receipt['exit_code']==0 and receipt['children_stopped'] and receipt['streams_drained'] and receipt['cleanup_complete'] and receipt['output_copied'] and not receipt['timed_out'] and receipt['capabilities']==[]
 assert j['frames']==j['acknowledged'] and j['protocol_complete'] and j['context_ready']
 assert j['identity']['pid']==receipt['pid'] and j['identity']['job']==receipt['job'] and j['identity']['appcontainer_sid']==receipt['appcontainer_sid']
 assert j['identity']['staging_directory'].lower().startswith(str(E/'fixture-temp').lower())
 observations[name]={'identity':j['identity'],'state':j['state'],'frame_count':j['frames'],'acknowledged':j['acknowledged'],'exit_code':receipt['exit_code'],'children_stopped':True,'streams_drained':True,'cleanup_complete':True,'output_copied':True,'capabilities':[],'manifest':j['manifest'],'request':request,'frame_types':[f.get('type',f.get('version')) for f in frames],'model_frames':[f for f in frames if f.get('type')=='effect.request']}
 if name=='pause':
  raw=(d/'checkpoint.sealed.json').read_bytes();c=j['checkpoint'];seal=j['checkpoint_seal'];assert len(raw)==c['bytes'] and len(raw)>65536 and len(raw)<=12*1024*1024 and digest(raw)==c['content_hash'];assert j['checkpoint_sequence']==6 and frames[-1]['sequence']==7 and frames[-1]['type']=='turn.paused';assert j['state']=='PAUSED' and j['pause_protocol']=='RESEARCHOS_PAUSE_V1'
  fact=(d/'checkpoint-6.json').read_bytes();assert digest(fact)==seal['journal_checkpoint_hash'];assert seal['content_hash']==c['content_hash'] and c['input_hash']==sha((d/'input/request.json').read_bytes());observations[name].update(checkpoint_bytes=len(raw),checkpoint_hash=c['content_hash'],checkpoint_sequence=6,paused_sequence=7,seal_receipt_kind='synthetic Core-shaped Artifact/use/journal')
 else:
  result=read(d/'output/result.json');observations[name]['result_model_calls']=result['model_calls']
  if name=='resume':assert result['model_calls']==3 and (d/'output/result.json').read_text(encoding='utf8').count('one original prompt')==1;assert request['epoch']==2
  else:assert result['model_calls']==1 and 'pause_protocol' not in request and j['checkpoint_sequence']==0 and not j['paused'] and j.get('checkpoint') is None
assert observations['pause']['identity']['pid']!=observations['resume']['identity']['pid'];assert observations['pause']['request']['run_id']==observations['resume']['request']['run_id'];assert observations['pause']['request']['epoch']==1
# The observation overlay changes only two log-adjacent capture calls and adds a file-copy helper; original assertions remain exact.
original=(E/'dependencies/adapters/runtime/bridge_control_windows_test.go').read_text(encoding='utf8');over=(E/'bridge_control_observation_windows_test.go').read_text(encoding='utf8');body=over.split('\nfunc reviewCaptureBridge(',1)[0];body=body.replace('reviewCaptureBridge(t, "pause", w.Directory())\n\t','').replace('reviewCaptureBridge(t, "resume", w2.Directory())\n\t','');assert body==original
for rel in ['adapters/runtime/process_windows.go','ops/experiment_sandbox/sandbox_windows.go']:
 p=E/'dependencies'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((S/rel).read_bytes())
audit={'input_pins_verified':len(pins),'source_clean':True,'source_scope_count':2,'author_manifest_members':12,'fresh_census':counts,'native_observations':observations,'overlay_original_assertions_unchanged':True,'source_read_finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};(E/'independent-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
temp=(E/'fixture-temp').resolve();assert temp.parent==E.resolve();temp.rmdir()
report=f'''# bridge checkpoint compat exact2 独立审查

结论：**SOURCE_ACCEPTED_LIMITED**，无 findings。接受限于本次源码分流修复、原有 legacy Core 路径回归及实际隔离 Native fixture 验证。未进行 Main 整合、安装包验证、产品模型调用或原产品 pause/resume；formal increment = 0。

## 冻结身份与输入

- Worktree `D:/作品集/ResearchOS/research-os/.local/worktrees/bridge-checkpoint-compat-20261014`；HEAD `0f9a870aed72785297a9999396fc8c760b296e13`；tree `fa071c9be7e39628c0b86ad43f77d5c50be63c7c`；base `a7ec7ebf2d53848ea163b6115667b3e3761a6bd2`。
- Scope CP475 SHA256 `b6af6ed6677b524673885a7b290022880045398b93c92420d28c620b21f25504`。exact2：`adapters/runtime/bridge_windows.go` SHA256 `71555893e2f4793acdd2ebc83ef57e98c6a5c84cf1742dbec00b42ea4581c224`；`adapters/runtime/bridge_legacy_checkpoint_windows_test.go` SHA256 `c7d8af8bc1e2d7b7cf5e988cce0075cd2ff025fae2b7ec0724392ec13a8cd575`。
- 作者 evidence-manifest SHA256 `e6f11bbf42a5f605106720dbdfba63a5873714ee98d1d5c58cf201f8e9194d35`，12成员逐项校验；report.json SHA256 `046e800454d9085a0c71302a1afca221d5e57cb08a4044c60611c3748604d4da`。包括 manifest 自身共13份作者文件已保存。
- 锁定 Go1.27.1、modules、compiler/toolchain、编译依赖及 Node/worker bundle共3772个输入文件在审查结束再次核验无漂移；raw go-list覆盖354 package条目。前后 Git clean、diff --check通过，原有两份 Core legacy test和worker/host setup依赖与base逐字节一致。

## 生产路径判断

1. `StartBridge` 在接收 worker输出前，从 Host给定的 immutable manifest 与 request 选择三种 mode。request 的 task/run/epoch必须对应manifest；显式协议只接受 RESEARCHOS_PAUSE_V1，包括 null/空字符串/布尔/unknown/重复键均拒绝。无协议的 Mu选择disabled，普通turn仍可执行；只有无协议的非Mu profile选择legacy。worker不能通过输出帧选择或切换mode。
2. checkpoint ingestion、ACK、turn.paused都按已冻结mode分流。V1保留原capture校验，<=64KiB元数据frame与<=12MiB checkpoint文件分别受限；要求绑定process/manifest/epoch、输入hash、native stream drain和完整typed Artifact/use/journal seal。缺元数据、inline fallback、弱ACK、空paused payload不能降级。legacy只允许有限inline JSON、空或checkpoint.json标签、无V1 key；ACK保持Core原有Artifact响应；paused不接受typed payload。未协商Mu不能走legacy checkpoint。
3. 离线恢复从Host原始dispatch input/request.json重读mode，与InputHash和外部传入的manifestHash绑定，并重核原task/run/epoch。journal mode擦除/改值、typed字段残留与disabled checkpoint均拒绝。原dispatch目录由Host私有ACL保护，worker只拿只读staged input；此边界没有把worker可写output当成模式来源。request reader复用实际句柄路径核对、final reparse拒绝、祖先路径解析、FILE_SHARE_READ与大小上限，目录junction负例已fresh通过。
4. 恢复继续要求原进程已停止、结束事实、stream drain、cleanup；paused新增context/protocol/全部ACK/exit0/outputCopied/非cancelled检查。V1恢复仍核checkpoint原始字节hash和durable seal。legacy Core保留 `native_resume=false`，未将旧context rebuild伪装成SDK原生恢复。

## 独立执行与原始观察

采用同一锁定工具链，mod=readonly、count=1、网络modules禁用，D盘共享cache和本审查唯一D盘temp。所有原始stdout JSONL、stderr、argv/cwd/environment/native exit均保留。

- 原始 V1 Native test及process/epoch绑定负例：2顶层、6子测试通过。为保留可复核原件，仅以Go overlay在原测试两条日志旁增加复制观察，原断言未改。实际运行生产Node+Mu bundle的两个AppContainer，暂停checkpoint **{observations['pause']['checkpoint_bytes']} bytes**（大于64KiB），sequence6→paused7，同Run epoch1→2，新旧PID不同，恢复消费原队列2条，模型计数累计3，原prompt未重放。
- 暂停、恢复、普通Mu各保存原始bridge journal、stdout/stderr、request；暂停另存checkpoint bytes和journal fact，恢复另存result。独立再次核对raw hash、frame序列、receipt身份、空capabilities、exit0、children stopped、streams drained、cleanup complete及output copied。记录来源为本轮实际sandbox执行，不仅引用作者报告。typed seal仍使用synthetic Core-shaped receipt，未宣称完整Core数据库Artifact/use接受。
- 原始 `TestRuntimeCoordinatorCheckpointResume` 和 `TestRuntimeCoordinatorCheckpointCrashRecovery` 未改，fresh 2/2通过；日志保存实际checkpoint_durable子进程exit86与新恢复子进程exit0，lease未延长、不完整terminal禁止resume。
- 完整跨模式/大小/重解析/离线降级负例，加两个独立测试：8顶层、47子测试通过。独立附加explicit null/false/duplicate protocol、非Mu及Mu V1 journal字段擦除拒绝；另以真实AppContainer完成**未协商V1的Mu普通turn**，1次合成MODEL响应、无checkpoint、exit0、原输出可读，证明旧Mu正常运行没有被整体拒绝。
- 总计12顶层、53子测试，全部native exit0，无skip。初始runtime精确名称过滤只选中了两项native测试，后续单独按prefix补齐负例，未重复native pause/resume。作者6次attempt及2次失败完整保留，未改失败计数。

## 边界与交付

本轮reviewer只写独立证据目录，Go overlay不修改源码。没有读取/修改原产品数据库、控制原产品进程、调用真实provider/model、构建安装包或写Main。临时测试目录已由测试清理，剩余空目录移除；正式原始观察和复现脚本保留。Root可据此整合本exact2；后续组合Core、最终包及真实产品资格/暂停验收需使用对应的新证据。作者与reviewer均未为本次增加正式用例接受。
'''
(E/'REVIEW.md').write_text(report,encoding='utf8')
r={'schema':'researchos.bridge-checkpoint-compat-independent-review/1','status':'SOURCE_ACCEPTED_LIMITED','findings':[],'head':'0f9a870aed72785297a9999396fc8c760b296e13','tree':'fa071c9be7e39628c0b86ad43f77d5c50be63c7c','scope_paths':read(E/'scope.json')['paths'],'input_pin_count':len(pins),'fresh_census':counts,'native_fixture_executed':True,'native_fixture_synthetic_model':True,'core_shaped_pause_receipts_synthetic':True,'product_db_touched':False,'product_processes_controlled':False,'live_provider_calls':0,'main_integrated_by_reviewer':False,'formal_increment':0,'source_read_finished_at':audit['source_read_finished_at'],'review_sha256':sha((E/'REVIEW.md').read_bytes())}
(E/'FINAL-report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
members=[{'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sorted(E.rglob('*')) if p.is_file() and p.name!='FINAL-manifest.json'];(E/'FINAL-manifest.json').write_text(json.dumps({'schema':'researchos.independent-source-review-artifacts.v1','artifacts':members},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':r['status'],'fresh_counts':{k:{a:b for a,b in v.items() if a!='log_outputs'} for k,v in counts.items()},'checkpoint_bytes':observations['pause']['checkpoint_bytes'],'pids':{k:v['identity']['pid'] for k,v in observations.items()},'review_sha256':sha((E/'REVIEW.md').read_bytes()),'report_sha256':sha((E/'FINAL-report.json').read_bytes()),'manifest_sha256':sha((E/'FINAL-manifest.json').read_bytes()),'members':len(members),'source_read_finished_at':r['source_read_finished_at']},ensure_ascii=True))
