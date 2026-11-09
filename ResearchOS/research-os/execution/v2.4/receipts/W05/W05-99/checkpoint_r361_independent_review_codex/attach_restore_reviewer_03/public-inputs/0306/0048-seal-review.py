import pathlib,json,hashlib,datetime
r=pathlib.Path(r'D:/作品集/ResearchOS/research-os');b=r/'execution/v2.4/receipts/W05/W05-99';a=b/'session_attach_restore_revision_codex/1a11e02f790732395c39325fbb4668d';o=b/'session_attach_restore_independent_review_codex/attach_restore_independent_review'
def pin(q):
 x=q.read_bytes();return {'path':str(q),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
def save(name,data):
 q=o/name
 with q.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 return pin(q)
io=json.loads((o/'review-io-input.json').read_bytes())
save('original-tool-io.json',{'scope':'Python source-review and rg calls after initial AGENTS read and ATT2 enumeration','records':io,'note':'markedPythonExit=null means Python not invoked or no actual marker; never inferred from outer exit.'})
closure=[]
for name in ['sourceguard.initial.json','sourceguard.supplemental.initial.json']:
 for before in json.loads((o/name).read_bytes())['refs']:
  q=pathlib.Path(before['path']);after=pin(q) if q.is_file() else None;closure.append({'before':before,'after':after,'unchanged':before==after})
save('sourceguard.final.json',{'scope':'READ_ONLY_SOURCEGUARD','observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'refs':closure,'all_unchanged':all(x['unchanged'] for x in closure),'mutated_outside_review_namespace':False,'runtime_SQL_Go_native_model_executed':False})
finding={'id':'ATTACH-RESTORE-002','severity':'Important','blocking':True,'file':str(a/'candidate-root/internal/domain/client_protocol.go'),'line':1304,'end_line':1329,'title':'RFC3339Nano textual order can hide the newest partial runtime observation','verification':'STATIC_SOURCE_COUNTEREXAMPLE_NOT_EXECUTED_IN_GO_SQL_NATIVE','evidence_ref':pin(o/'timestamp-counterexample.json'),'impact':'The latest partial observation can be ignored, allowing old settled evidence plus a recovered handoff to renew the writer lease; without a recovered handoff, stale-ready evidence can enter transfer.','fix':'Determine latest evidence using parsed timestamps, with conservative handling for ties/invalid timestamps, before validating latest settlement. Add a mixed-fractional-precision older-settled/newer-partial regression.'}
save('findings.json',[finding])
report="""独立 Source 审查结论：REQUEST_CHANGES。发现 1 项 Important 阻塞问题 ATTACH-RESTORE-002；不批准整合或原生验收。

原 ATTACH-RESTORE-001 的十类缺失/错绑定/陈旧/部分观察分支已在 Source 中补上门禁：client_protocol.go:1128 在任何 attach lease UPDATE 之前调用 helper。没有 Run 或没有 restore barrier 时仍允许同 owner 正常 active renewal。有 barrier 时，Run 的当前 lease_epoch、children_stopped 与 queue_empty 必须有效；观察同时匹配 project/run/epoch/spec task/run/epoch、Hash(body)、strictly after barrier，以及两项 settled。以上为静态路径判断，未执行 Go。

恢复 generation 需要 durable CLIENT_HANDOFF：session/run/protocol/command/sequence 对齐，event sequence 不超过当前 watermark，target/writer owner 等于当前 owner，writer epoch 等于当前 Session epoch，previous epoch=current-1，effective 严格晚于 barrier 且不早于 fresh observation，expiry 晚于 effective。没有恢复 generation 的旧未来 lease 无法直接 renew，而会进入原 HandoffEpoch/CAS/journal transaction。新 barrier 会使旧 handoff 失效。helper 不写 Run、barrier、queue/control 或 resume 标志。

ATTACH-RESTORE-002（Important，阻塞）：1304 用 ORDER BY observed_at DESC 选“最新”记录，1325 仅对第一行执行 latest 拒绝逻辑。store.go:131 的 Now() 输出 RFC3339Nano，可变小数位字符串不保证按时间排序。例如同秒 .1Z 的 settled 记录在文本倒序中排在 .11Z 的 queue_empty=false 记录之前；第二行因为 latest=false 被略过，firstFresh 保留较早记录。若当前 Session 有匹配的 post-barrier handoff 与 future lease，helper 返回 renew=true。runtime.go:98-107 的 native dispatch 校验要求匹配 identity、递增 sequence、children_stopped、streams_drained、cleanup_complete、ended，但不要求 queue_empty=true，113 才写 observation；因此后一个 partial shape 在该生产边界并未被静态排除。当前 Run 的旧双 settled flags 不能代替更新的 observation。没有 handoff 时同样可能以旧 ready 状态进入 transfer。

timestamp-counterexample.json 分开保存实际 Python 字符串排序/时间比较/分支翻译结果与源码可达性推断。这不是 native、SQL 或 Go 复现。修复应根据解析后的 time.Time 决定真实最新观察，先确认最新事实有效，再使用最早的合格 fresh 时间判定 generation；补一个混合小数精度、较早 settled/较晚 partial 的回归。

新测试的 10 modes × 2 owners 静态调用链可达：orchestrationSetup -> task/claim -> handlerTypedSession -> attachContractCommand（新 command、当前 revision、null writer_epoch）-> handlerCommand -> DecodeEnvelope -> Execute（f.owner principal）-> dispatch -> handleWrite -> restore helper。same/different owner 不会提前被普通 writer-client 检查挡住，因为 takeover 分支只要求不携带 epoch。每类观察都是故意无效的负向夹具；未伪造有效 fresh 正向证据。旧 attach tests 字节完全不变。新 ordinary active test 委托旧测试，属于开发夹具覆盖，不是 native 证明。

事务和幂等：Execute/dispatch 前缀与原 Source 相同，exact replay 在 dispatch 前返回持久响应；REJECTED 回滚 command savepoint 的业务写并记录幂等结果。HandoffEpoch 的 epoch+1/revision+1、writer attribution、CLIENT_HANDOFF 和水位 revision+1 沿用同一事务；journal 整段与 session.control 段逐字相同。7 项静态文本检查通过不等于测试通过。

HDF/MF 双锁已先核验，然后核验 ATT2 13 个 manifest 成员、前一次独立审查 44 个成员及 public-input pins。Sourceguard.initial/final 保存所有输入的 SHA256、bytes 和关闭时观察；supplemental pins 覆盖 Main 四个相关文件、canonical 四文件和 T6 domain Go 文件。源文件 hash/bytes 见 pin-table.md；任何外部并发变动应以 final guard 明细为准。

真实 fresh restore positive 保持 BLOCKED/PENDING_ROOT_RESOURCE。尚未验证 one-generation transfer、exact replay、recovered renewal/new later observation/new barrier/current-epoch-change 的真实路径。编译、测试、SQL、native、模型及外部网络均未执行。Root 的 liveNative Job 未触碰。Main/canonical/作者包/旧树未写入。旧错误 832/834、827/829/831 保留；本次机械错误 838 为 CreateProcess 命令过长，实际 outer/Python/native exit 均为 null；原始输入和渲染异常已保存，不重置 ordinal。active asynchronous takeover 与 historical cached ACK reconciliation 仍为开放分支。

Authority=SOURCE_ONLY_INDEPENDENT_REVIEW；formal=false；production_ready=false；Main_adopted=false；STOP=true。
"""
(o/'report.md').write_text(report,encoding='utf-8',newline='\n')
refs=[pin(a/'HDF.json'),pin(a/'MF.json')]+[pin(a/'candidate-root/internal/domain'/name) for name in ['client_protocol.go','client_protocol_attach_contract_windows_test.go','client_protocol_attach_restore_windows_test.go']]
table='| Input | SHA256 | Bytes |\n|---|---|---:|\n'+'\n'.join('| '+ref['path']+' | '+ref['sha256']+' | '+str(ref['bytes'])+' |' for ref in refs)+'\n'
(o/'pin-table.md').write_text(table,encoding='utf-8',newline='\n')
h={'schema':'researchos.independent-attach-restore-source-handoff.v1','verdict':'REQUEST_CHANGES','status':'SOURCE_REJECTED_LATEST_OBSERVATION_ORDERING','actor_id':'codex:/root/attach_restore_independent_review','source_component_accepted':False,'source_handoff_ref':pin(a/'HDF.json'),'source_manifest_ref':pin(a/'MF.json'),'report_ref':pin(o/'report.md'),'findings_ref':pin(o/'findings.json'),'sourceguard_initial_ref':pin(o/'sourceguard.initial.json'),'sourceguard_supplemental_initial_ref':pin(o/'sourceguard.supplemental.initial.json'),'sourceguard_final_ref':pin(o/'sourceguard.final.json'),'static_checks_ref':pin(o/'static-checks.json'),'counterexample_ref':pin(o/'timestamp-counterexample.json'),'tool_io_ref':pin(o/'original-tool-io.json'),'important_blocking_count':1,'critical_count':0,'original_finding':'ATTACH-RESTORE-001 direct absent/stale/misbound/partial path addressed statically; latest-observation ordering remains blocking','positive_restore_acceptance':'BLOCKED/PENDING_ROOT_RESOURCE','tests_executed':False,'build_executed':False,'SQL_native_model_executed':False,'formal':False,'production_ready':False,'execution_authority':False,'authority':'SOURCE_ONLY_INDEPENDENT_REVIEW','Main_adopted':False,'FULL_pass':False,'mechanical_failure_ordinals':[838],'preserved_prior_failure_ordinals':[827,829,831,832,834],'failure_counter_reset':False,'open_branches':['active asynchronous takeover','historical cached ACK reconciliation'],'all_sourceguard_pins_unchanged':all(x['unchanged'] for x in closure),'next_actor':'Root reviews independent finding, assigns immutable source revision, and owns any future composition/runtime authorization','STOP':True}
save('HDF.json',h)
members=[pin(q) for q in sorted(o.iterdir()) if q.is_file() and q.name!='MF.json']
save('MF.json',{'schema':'researchos.independent-source-review-manifest.v1','members':members})
print(json.dumps({'HDF':pin(o/'HDF.json'),'MF':pin(o/'MF.json'),'guard_ref_count':len(closure),'all_unchanged':all(x['unchanged'] for x in closure),'drift':[x for x in closure if not x['unchanged']],'verdict':'REQUEST_CHANGES'},ensure_ascii=False))

