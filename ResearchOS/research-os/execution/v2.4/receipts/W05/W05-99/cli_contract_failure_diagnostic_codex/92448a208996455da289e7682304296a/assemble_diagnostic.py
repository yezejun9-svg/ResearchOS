from pathlib import Path
import json, hashlib

N = Path(__file__).parent
L = json.loads((N / 'location.json').read_text(encoding='utf-8'))
W = Path(L['wt'])
S = Path(L['main']).parent / 'ResearchOS_Implementation_Package_v2.4'
B = W / 'execution/v2.4/receipts/W05/W05-99/host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/contract-native-runner-18fc6ba4559e47e3944c6c7bd0032a8d/run-1f5a7a1af626420792706b764cd6ef37'
def write(name, obj):
    (N / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def ref(path, locator=None):
    p = Path(path)
    out = {'path':str(p), 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    if locator is not None: out['locator'] = locator
    return out
def loc(path, first, last):
    return ref(W / path, {'line_start':first, 'line_end':last})

report = json.loads((B / 'command.stdout').read_text(encoding='utf-8'))
# Each tuple is one original failure in its original array order. These are static diagnoses, not test results.
data = [
('FIXTURE_PRECONDITION', 'main.go',260,264,
 '原 exit=3/reason=INIT_REQUIRES_HOST_PROJECT_BOOTSTRAP 正确；失败的是旧 workspace_ref 回显及 WORKSPACE_VALIDATED_AND_RECORDED 断言。生产此时仅路径校验、不落盘配置、不把绝对路径冒充授权引用。',
 'cli_contract.go',322,351,
 '保留中文/空格路径实际输入及 exit3；断言 WORKSPACE_PATH_VALIDATED 与配置文件仍不存在。真实路径识别/授权引用应在另一本机 choose→register→bootstrap 正例证明，不令 hostless init 创建假 workspace_ref。',
 '冻结22 §2.2–2.3；本行缺授权路径正例，不能据安全拒绝宣布 init 完成。'),
('FIXTURE_CHAIN', 'main.go',273,285,
 'main 从删除配置开始；hostless init 不创建配置，随后 config show 实际 CONFIG_UNREADABLE/1。旧行把不存在的配置当已存在且应 unchanged。',
 'cli_contract.go',339,351,
 '将拒绝不改变既有配置与首次无配置两案隔离：现有配置案由合法配置/初始化取得原 bytes 后比较；无配置案保持不存在。不能通过写伪授权 workspace 制造成功。',
 '需有原配置 bytes→refusal→同 bytes 及 absent→absent 两条新证据。'),
('FIXTURE_PROTOCOL_AND_SCOPE', 'v2verbs.go',359,365,
 'goal.start 确已上 wire，原 reply 缺 method，先 REPLY_IDENTITY_MISMATCH；同时此案没有 Session，旧预期 revision=7/epoch=2 与生产 project-level null 分支不符。',
 'cli_v2.go',148,179,
 '探针返回完整 StartGoalResult+原请求身份；分开无Session的project Goal 与已有Session CAS 两案，不能给project级请求伪造Session或用通用method_confirmed替代结果。非draft还需可追踪执行结果。',
 'schema CommandEnvelope goal.start scoped条件；22 §3–4。原fail stdout被clip，完整后续未发生。'),
('FIXTURE_PROTOCOL', 'v2verbs.go',370,375,
 'go 请求 goal.start，但 generic reply 缺 method，身份验证提前拒绝；当前 detail 来自额外 go x 调用，不是闭包内同一次 check the citations 调用。',
 'cli_v2.go',270,282,
 '保留别名和实际objective断言；使用合法Goal结果及完整追踪链；一次调用原始raw同时用于断言和诊断，勿增加第二调用充当第一调用证据。',
 '与 goal 同一合法结果/执行门；本行不能因wire存在改成执行成功。'),
('FIXTURE_PROTOCOL_AND_PRODUCT_OPEN', 'v2verbs.go',377,385,
 'attach 已送出，generic AttachResult 缺 method/真实snapshot，exit1，control未发生。修response后还存在本报告 P02 RESUME 恢复语义缺口。',
 'cli_verbs.go',77,110,
 '合法AttachResult及已绑定Goal/Run/snapshot；保留同Session/epoch/sequence原断言。RESUME目标和实际恢复需单独产品scope，不能在probe里无条件COMPLETED。',
 '22 §1/5.2；当前只见attach原请求，未见真实恢复。'),
('OBSOLETE_USAGE_EXPECTATION_AND_PRODUCT_OPEN', 'v2verbs.go',386,389,
 '无writer-epoch现在走session.get→attach(true)接管，先被旧snapshot缺method拒绝；旧测试要求 MISSING_WRITER_EPOCH。detail另一次SID=s调用，不能替代闭包SID=sess-42原raw。',
 'cli_verbs.go',87,95,
 '按冻结resume <session-id>验证先读snapshot、attach true仅携带current expected_revision且writer_epoch=null、取得新epoch后才能写；拒绝争抢时不control。保留显式非法epoch输入负例。',
 '22 §5.1明确不得借源客户端epoch接管；真实恢复仍 P02 OPEN。'),
('FIXTURE_PROTOCOL_AND_HELD_F08', 'v2verbs.go',395,400,
 'cancel先真实读取session.get；旧generic snapshot缺method，退出1，未到session.control。不是已证明取消生产路径失效。',
 'cli_stream.go',619,634,
 '构造真实当前Task/Run/Goal归属与snapshot，保留CANCEL原目标；必须观察control及子进程/queue/effect实际停止。ACK不能算完成，不重跑held F08链。',
 'F08 ACK→final immutable1811继续独立OPEN；本行未达该故障，不重复计新origin。'),
('FIXTURE_STATE_AND_PROTOCOL', 'v2verbs.go',406,420,
 '/status继承前案保存的Session，先session.get被旧reply拒绝，故没有host.status。',
 'cli_verbs.go',68,76,
 '每slash案明确隔离有/无Session配置，合法snapshot后仍必须实际host.status，不把前置读取删除。',
 '原wire仅session.get；同scope顺序存在不表示完整两leg已证。'),
('FIXTURE_STATE_AND_PROTOCOL', 'v2verbs.go',406,420,
 '/goal继承Session，先session.get被旧reply拒绝，尚未goal.start。',
 'cli_verbs.go',124,129,
 '真实scoped snapshot+writer+Goal typed响应；新命令ID和合法CAS，保持别名行为及objective。',
 '需scoped Goal实际wire及结果/不可变来源，不能删除前置snapshot。'),
('FIXTURE_PROTOCOL_AND_PRODUCT_OPEN', 'v2verbs.go',406,420,
 '/resume实际session.attach已发但reply缺method而code1，旧行要求code0。',
 'cli_verbs.go',77,110,
 '用合法AttachResult恢复alias测试；真实RESUME控制按P02另闭合，不由fixture假成功。',
 '尚缺typed attach及原恢复链成功，P02保持OPEN。'),
('FIXTURE_STATE_AND_PROTOCOL', 'v2verbs.go',406,420,
 '/cancel先session.get被旧reply拒绝，没有control；当前SID来自前案而非本案独立setup。',
 'cli_stream.go',619,634,
 '为本案设置同Session所属真实Run/Goal并合法snapshot，保留alias、目标及停止断言；F08 held不跨scope处理。',
 '未到实际cancel终态，不能补造成功。'),
('FIXTURE_PROTOCOL_AND_EXIT_EXPECTATION', 'v2verbs.go',422,428,
 '旧REJECTED WRITER_BUSY reply缺method，实际先identity mismatch/1。补method仍不能把WRITER_BUSY资源/授权阻塞要求为1：生产映射3。',
 'cli_v2.go',285,294,
 '保留原“拒绝不为0”意义；返回完整ProtocolError/原method、SID、revision，按product exit3验证WRITER_BUSY；用另一真实execution failure验证1。',
 'product.cli.exit_codes /3；当前原报告没有合法WRITER_BUSY响应被消费的证据。'),
('FIXTURE_INVALID_STATUS_AND_PRODUCT_MAPPING_GAP', 'v2verbs.go',429,432,
 '原顶层status NOT_IMPLEMENTED缺method而exit1；冻结CommandResponse仅三种status，不允许这个顶层状态。且当前先session.get，旧期望reason host.status不对应真实故障方法。',
 'cli_v2.go',270,298,
 '主正例使用REJECTED/error_code NOT_IMPLEMENTED+完整error，绑定实际请求method；按旧检查资源不可用exit3意图须同时审P04，当前合法REJECTED该code落默认1。旧非法status可保留成拒绝负例，不把非法响应变合法。',
 'schema /$defs/CommandResponse/properties/status；legacy容忍分支不能作为/v2协议资格。'),
('OBSOLETE_REASON_EXPECTATION', 'v2verbs.go',439,449,
 '原HTTP500已经exit1/HOST_HTTP_500；仅旧 UNKNOWN_STATUS 前缀不匹配，未发生completion。',
 'cli_v2.go',255,260,
 '保留真实500和exit1，匹配HTTP错误分类且不采用body为成功；不将早HTTP分类回退成无状态JSON错误。',
 'L01静态分支原cohort至冻结同SHA；本行安全结果已见，但原check仍FAIL不可改写。'),
('FIXTURE_ENV_AND_RAW_GAP', 'v2verbs.go',453,460,
 '原记录只给exit3/saw[]，没有实际reason。调用使用移除credential后的os.Environ，而非base()，丢本阶段discovery/config/client注入；因此不能证明失败确在CREDENTIAL_ABSENT。',
 'cli_verbs.go',173,199,
 '从本案base环境仅移除credential，并使用本案临时空native session资源/不可续期条件，隔离外部发现；捕获真实reason和所有wire零请求。不读取用户session文件。',
 '实际原reason未保存，不能断言已观测HOST_DISCOVERY_UNAVAILABLE；环境解释是源码推断。'),
('FIXTURE_PROTOCOL', 'v2verbs.go',563,566,
 'strict模式只验证请求，回复仍generic且缺method；session.get REPLY_IDENTITY_MISMATCH使status失败。',
 'cli_stream.go',636,645,
 '保留严格请求检查，同时回应真实SessionSnapshot及HostStatusResult；若snapshot有Goal还需真实只读continuation接口。',
 '不能只修method后把任意result当真实snapshot；P03响应完整校验另列。'),
('FIXTURE_PROTOCOL_AND_SCOPE', 'v2verbs.go',567,573,
 '原最后envelope是失败的session.get，根本未goal.start；检查p.last CAS并不是目标方法的原证据。',
 'cli_verbs.go',124,129,
 '合法scoped snapshot后按method定位goal.start；比较读取writer/revision与写命令；另保留project-level null案，严格探针不能一律要求CAS。',
 '目标method+作用域+原request identity全部验；当前无goal.start成功证据。'),
('FIXTURE_INVALID_STATUS_AND_ADMISSION', 'v2verbs.go',575,589,
 'HTTP202原IN_PROGRESS缺method/result，先identity mismatch。即便修method，IN_PROGRESS不是冻结/v2合法status；持久接收也不授权立即RESUME控制或称完成。',
 'cli_stream.go',200,224,
 '主案改合法ACKNOWLEDGED/PendingResult，同command重放最终COMPLETED/AttachResult后才后续control；保留长期pending非完成和取消控。原IN_PROGRESS仅作为兼容/非法负例单列。',
 '冻结22 §4；当前attach wait=false，ACK后续写是否阻断需独立产品负控，不靠新fixture立即success遮蔽。'),
('AGGREGATE_DOWNSTREAM', 'v2verbs.go',598,611,
 'wire map确缺session.control，前面attach/get皆被旧fixture截断。该汇总继承前项，不是第19个独立生产故障。',
 'cli_verbs.go',77,110,
 '保持全部leg roster，先修合法前提并真正执行原leg；聚合从原wire累积，不能静态填充或删除未观测方法。',
 '不能与单项叶子重复计为独立故障origin；原entry完整保留。'),
('FIXTURE_NATIVE_AUTHORITY', 'v2verbs.go',613,625,
 'init实际NATIVE_WORKSPACE_CHOICE_FAILED/HOST_NATIVE_DISCOVERY_INCOMPLETE，project.bootstrap没有发出。probe只写url/pid/data_dir=x，无真实native Host identity/选择授权；旧预期authorized_workspace_ref=目录字符串亦不合法。',
 'cli_native.go',31,72,
 '实际同SID临时Host/受信native choose→单次selection→workspace.register→opaque authorized ref→project.bootstrap；录真实目录与原bytes但不把原路径当授权ref。不能伪host_instance_id或HTTP建OWNER。',
 '22 §2；需要未来授权本机fixture链，原HTTP probe不足，本任务0native执行。'),
('FIXTURE_PROTOCOL_AND_RUNTIME_EVIDENCE', 'v2verbs.go',627,634,
 'run先session.get identity mismatch，未send/events。原endsWith send,events也不足证明真正Task结果/不可变模型工具产物。',
 'cli_stream.go',642,657,
 '完整snapshot→合法NORMAL SendMessageResult→实际同Task/Run事件和终态；保留send/events wire且允许合法中间只读轮询，不把ADMITTED当成功执行。',
 'fixture Runtime证据与LIVE资格分开；原报告不能证明普通模型/工具完成。'),
('FIXTURE_STATE_AND_STREAM_SHAPE', 'v2verbs.go',641,650,
 '前run把sess-probe保存到同config，interactive继承它，实际list→get而非create，再被旧reply拒绝。jsonOf取第一JSONL，不适用于现在多条事件/每turn summary；messages_read_from_stdin并非当前输出。',
 'cli_verbs.go',224,319,
 '真正无Session setup、合法list/create/owner与stream事件，按所有JSONL归属验证两条输入恰各一次，不能要求连续无get/events的四method串或仅第一行summary。既有Session另案。',
 '14 §4 TUI/多行/流式完整能力不能由此行两stdin成功替代；P01仍独立缺证。'),
('FIXTURE_PROTOCOL_AND_PRODUCT_GAP', 'v2verbs.go',651,657,
 '实际list→get在reply拒绝；另外完整静态interactive分支没有session.attach调用。修合法snapshot后仍不能保证该必需leg，不能删掉原attach断言。',
 'cli_verbs.go',224,319,
 '需独立最小产品scope：selected Session先合法只读/明确接管attach，按真实owner授予后再send；无权时不抢owner。保留原SID、全部method和单次send证明。',
 'P01：product.cli interactive local_operations包含session.attach；这是静态真实产品缺口，未运行复现/修复。'),
('FIXTURE_PROTOCOL_AND_IDENTITY_GUARD', 'v2verbs.go',684,700,
 '新建Session的generic reply缺method，exit1。伪list返回Session字段但未被采用，真正create尚未合法通过；无法证明整条不替换会话。',
 'cli_v2.go',333,365,
 'list返回合法SessionListResult内other item，create返回合法新snapshot；后续完整wire/事件及本地state只能来自create。另将非法list/session错配作拒绝负例，不用不合法正例自证。',
 '当前adopt仅method=session.create才允许新SID；该静态守卫不等于完整响应来源验真/P03闭合。'),
('OBSOLETE_STATUS_EXPECTATION', 'main.go',539,540,
 '实际code130/exit_code130均成立，失败仅顶层status INTERRUPTED_READ_ONLY而旧期望INTERRUPTED。reason为READ_INTERRUPTED；这是只读status中断，不是活动Run取消证明。',
 'cli_stream.go',690,700,
 '保留实际WindowsCTRL_BREAK child和130，明确只读INTERRUPTED_READ_ONLY；另保留活动取消实际settled门，不能用readonly130关闭F08或子进程停止。',
 'product exit130语义与L02实际分支；原entry仍FAIL，不覆盖旧报告。'),
('AGGREGATE_DOWNSTREAM', 'main.go',413,465,
 'tableRowsProven只收ok成功IDs；上述失败ID不在成功集合，逐row映射失败。因此本条是依赖汇总，不是另一未知业务故障。detail每参数最多600bytes，原表gap字符串已截断。',
 'cli_contract.go',45,76,
 '保留全部原proven_by和检查ID，合法逐项执行后让汇总自行通过；不删rows/填PASS或将69当总通过。可新增细化case，不能合并旧失败为不运行。',
 '尚未有current formal harness；其余69旧成功也不能无条件继承当前38资格。')
]
assert len(data)==26 and len(report['failures'])==26
rows=[]
for i,(kind,h,a,b,cause,p,pa,pb,change,gap) in enumerate(data):
    f=report['failures'][i]
    lines=(W/'tests/runtime/cli_contract'/h).read_text(encoding='utf-8').splitlines()
    exact=[j+1 for j,l in enumerate(lines) if 'ok("'+f['id']+'"' in l]
    if exact:
        a=exact[0]
        b=a
        while b<len(lines) and not lines[b-1].rstrip().endswith(')'):
            b+=1
    rows.append({'ordinal':i+1,'id':f['id'],'original_failure':f,
      'original_raw_ref':ref(B/'command.stdout',{'json_pointer':f'/failures/{i}'}),
      'classification':kind,'actual_cause_and_inference_boundary':cause,
      'harness_locator':loc('tests/runtime/cli_contract/'+h,a,b),
      'shared_fixture_reply_locator':loc('tests/runtime/cli_contract/v2verbs.go',128,246) if h=='v2verbs.go' else None,
      'producer_locator':loc('apps/cli/'+p,pa,pb),
      'minimal_compatible_proposal':change,'unverified_boundary':gap,
      'current_formal_status':'NOT_REEXECUTED_OR_ACCEPTED',
      'current_fix_claim':'NONE; static comparison only; consult historical-current-comparison.json. No row is promoted to PASS.'})

write('diagnostic_matrix.json',{'schema':'researchos.readonly-cli-contract-diagnostic.v1',
 'actor':'codex:/root/sources_parent_impl','role':'HANDLER_AUTHOR_READONLY_DIAGNOSTIC_NOT_ACCEPTOR',
 'status':'NO_SOURCE_READY_DIAGNOSTIC_ONLY','frozen_handler_source_commit':'22752a6a41732c8c158d7d7e1b8932ec958f8cb8',
 'original_invocation_ref':ref(B/'command.invocation.json'),'original_result_ref':ref(B/'result.json'),
 'original_report_ref':ref(B/'command.stdout'),'original_counts':{'successful_check_ids':len(report['assertion_ids']),'failure_entries':len(report['failures']),'not_verified_entries':len(report['not_verified']),'report_status':report['status'],'whole_suite_pass':False},
 'count_semantics_ref':loc('tests/runtime/cli_contract/main.go',36,49),
 'evidence_limits':['No new harness execution. Historical code/executable and current source differ; no current PASS inheritance.','ok detail clips each argument to 600 bytes; some details are from a second invocation. Child stdout/reason not preserved by the original report cannot be recovered by inference.','26 failure entries are not 26 independent root causes or new failure origins.','The readonly input capture is not a full compiler/tool/SDK execution closure.'],
 'rows':rows})

write('product_gaps_and_scope_proposal.json',{'status':'PROPOSAL_ONLY_NO_WRITE_AUTHORIZATION',
 'scope_phases':[
 {'phase':1,'proposed_paths':['tests/runtime/cli_contract/main.go','tests/runtime/cli_contract/v2verbs.go'],
  'bounds':['Preserve all original check IDs and actual command/method/permission assertions. Exact obsolete assertion adaptations require nonauthor review and Root scope.','Isolate per-case config and env; complete typed probe replies from frozen schema; preserve protocol-negative controls separately.','Real native init requires actual owned temporary Host/SID resources; do not fabricate OWNER or workspace authorization.','Pending progression must replay same command and wait for actual COMPLETED; no claim of cancelled completion from ACK.','Report every actual child argv/exit/stdout/stderr and JSONL lines without lossy extra invocations.'],
  'held':'No rerun before actual approved source/fixture change and current source freeze. Existing formal harness is held in this task.'},
 {'phase':2,'id':'P01','finding':'Existing-session interactive branch has no explicit session.attach path; fixing generic fixture does not implement the required leg.',
  'source_refs':[loc('apps/cli/cli_verbs.go',224,319),loc('apps/cli/cli_verbs.go',147,165)],
  'contract_ref':ref(S/'contracts/product.contract.json',{'json_pointer':'/cli/commands/0'}),
  'minimal_candidate_paths':['apps/cli/cli_verbs.go','new dedicated CLI interactive integration test path to be registered'],
  'proof_required':'Actual compiled CLI + legitimate existing Session, read-only attach vs explicit owner transfer, no send before authority, exact one send, immutable original identity and competing-owner rejection.'},
 {'phase':3,'id':'P02','finding':'Current RESUME session special branch checks settled predecessor and returns snapshot; it rejects active/paused-unsettled Run and does not drive the frozen real pause/resume/checkpoint lifecycle. Legacy Session convenience must not be reported as full runtime resume.',
  'source_refs':[loc('apps/cli/cli_verbs.go',77,110),loc('internal/domain/client_protocol.go',1188,1228)],
  'contract_ref':ref(S/'22_CLIENT_INTERFACE_DETAILS.md'),
  'scope_boundary':'Needs independent runtime/host control design before exact production scope; client_protocol.go and cli_verbs.go are implicated, but this audit cannot assert those two paths alone suffice. No F08 implementation or held1811 replay authorized.',
  'proof_required':'Same original Goal/Task/checkpoint and authorized writer; PAUSE then explicit RESUME actualdispatch; cancelled oldRun never resurrected; new authorized attempt provenance; pending/unknown remains visible.'},
 {'phase':4,'id':'P03','finding':'Generic v2Call used by interactive session.list disables strict identity; generic flow transport checks identity but does not validate every method complete result. Adding method only to generic mock would still not prove the frozen full typed response contract.',
  'source_refs':[loc('apps/cli/cli_v2.go',216,298),loc('apps/cli/cli_verbs.go',237,241),loc('apps/cli/cli_stream.go',200,224)],
  'scope_boundary':'Potential dedicated response validation revision, separate from already strict configure/doctor. Do not weaken generic rejection gates or modify protected tests. Needs exact caller inventory before source registration.',
  'proof_required':'Wrong method/command/SID/project, invalid SessionSnapshot/SessionListResult, legal PendingResult and admission ordering; actual native CLI negative controls with no state adoption or write. Explicitly test attach(true) ACK with no granted writer: no session.control until actual completed transfer.'},
 {'phase':5,'id':'P04','finding':'Legacy top-level NOT_IMPLEMENTED maps to3, but a frozen-schema legal REJECTED/error_code=NOT_IMPLEMENTED currently falls through to generic exit1. Fixture-only replacement cannot retain the original unavailable-operation exit3 assertion.',
  'source_refs':[loc('apps/cli/cli_v2.go',285,298)],
  'scope_boundary':'Nonauthor must decide the exact exit classification against frozen product semantics; if exit3 is confirmed, narrow cli_v2.go error classification plus dedicated response control test. Do not change the frozen enum or generic failure handling.',
  'proof_required':'Actual compiled CLI consumes complete legal typed NOT_IMPLEMENTED rejection, no completion/state adoption, resource/unavailable exit3 and genuine execution failure exit1 remain distinct.'}],
 'wider_product_boundary':'14 §4 explicitly requires interactive TUI and actual tools/edit/build/test/resume. This 26-row diagnostic and old two-stdin probe cannot establish those capabilities. Parent A04/P01/U02 remain separate actual evidence gates.',
 'forbidden_shortcuts':['Do not restore project goal artificial CAS fields.','Do not accept IN_PROGRESS/NOT_IMPLEMENTED as frozen top-level status.','Do not skip failing IDs/table rows.','Do not use header/status echoes or mock labels as model/runtime qualification.','Do not relax native workspace/OS-principal authorization or F08 immutable protection.']})

spec=json.loads((S/'contracts/client.protocol.schema.json').read_text(encoding='utf-8'))
write('contract_facts.json',{'product_cli':json.loads((S/'contracts/product.contract.json').read_text(encoding='utf-8'))['cli'],
 'schema_ref':ref(S/'contracts/client.protocol.schema.json'),
 'response_statuses':spec['$defs']['CommandResponse']['properties']['status'],
 'response_required':spec['$defs']['CommandResponse']['required'],
 'typed_results':{k:spec['$defs'][k] for k in ['SessionSnapshot','SessionListResult','AttachResult','StartGoalResult','PendingResult','ControlResult']},
 'envelope_conditions':spec['$defs']['CommandEnvelope']['allOf']})

before=json.loads((N/'input.before.json').read_text(encoding='utf-8'))
after=[{'path':x['path'],'sha256':hashlib.sha256(Path(x['path']).read_bytes()).hexdigest(),'bytes':Path(x['path']).stat().st_size} for x in before]
write('input.after.json',after)
write('input_audit.json',{'capture_scope':'61 explicit public source/spec/history inputs; not compiler closure', 'count':len(before),'before_equals_after':before==after,
 'initial_read_limit':'Initial 8-file hash snapshot followed first report reads. Expanded61 begins after preliminary reading; no claim of a pre-read hash of every input. Both snapshots are retained.',
 'frozen38_git_binding_ref':ref(N/'frozen38-git-binding.json'),
 'historical_comparison_ref':ref(N/'historical-current-comparison.json')})
print(json.dumps({'matrix_count':len(rows),'input_count':len(before),'input_drift':before!=after,'status':'NO_SOURCE_READY_DIAGNOSTIC_ONLY'},ensure_ascii=False))
