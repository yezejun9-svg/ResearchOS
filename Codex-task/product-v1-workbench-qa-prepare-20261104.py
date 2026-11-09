from pathlib import Path
import datetime,hashlib,json

HERE=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-workbench-independent-qa-20261104')
ROOT=Path('D:/作品集/ResearchOS/research-os')
scope_path=ROOT/'execution/product-v1/receipts/single-harness-20261104/workbench/scope.json'
contract_path=ROOT/'execution/product-v1/contracts/harness.v1.interface.rev2.json'
d03_path=ROOT/'docs/product-v1/D03-native-platform-policy.md'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
scope=json.loads(scope_path.read_text(encoding='utf-8'))
contract=json.loads(contract_path.read_text(encoding='utf-8'))
assert sha(contract_path)=='046a49b2b1f82593fe86924913b2ee4d77152ac1cef7dbbb86562f6dfe0cfa1c'
assert contract['contract_revision']==2
assert len(scope['production_paths'])==8 and len(scope['test_paths'])==2
rows=[
 ('Q01','queued_ack','POST202为QUEUED、run=null、revision字符串。随后GET仍QUEUED。','不得假建run/epoch或显示COMPLETED/成功结果；停止请求使用null/null和真实revision。','submit_and_recovery_rules; $defs/SubmitData'),
 ('Q02','whole_message','ASSISTANT_MESSAGE是完整消息；TOOL_EVENT失败；LOG中包含貌似成功JSON。','不伪造token delta/工具成功；LOG只作诊断，整条assistant消息不能按字逐个声称native流。','capabilities_rules; event_payload_rules'),
 ('Q03','int64_exact','sequence/cursor/revision/epoch为9007199254740993及9223372036854775807字符串。','逐字节保真排序/比较和传参；不经过Number或降限到2^53；拒绝9223372036854775808、01、1e3、负值、JS数字。','cursor_rules; $defs/Decimal; $defs/PositiveDecimal'),
 ('Q04','cursor_namespaces','recent-list cursor大于当前task event cursor，切项目/任务/返回原任务。','list/event两个游标不互相覆盖；project/task切换从各自正确状态/0开始；不串Task历史。','cursor_rules'),
 ('Q05','cursor_reset','先有旧事件缓冲，再收到reset=true、events=[]、snapshot=current Task、next_cursor较低。','仅reset按snapshot替换派生状态并丢旧增量；绝不POST；end=false才从新cursor继续只读轮询。普通页倒退需拒绝/报告。','cursor_rules'),
 ('Q06','event_pages','重放相同event_id/sequence，Run epoch变化，terminal Task但has_more=true，空页end=false。','稳定去重；epoch变不清游标；末个持久terminal事件耗尽前不当end；空页保留cursor，bounded backoff。','cursor_rules'),
 ('Q07','late_scope','Host A请求挂起后切Host B；再切project、harness、task、generation，然后A迟到返回。','capability/list/task/events/submit/cancel结果只能作用于捕获的完整上下文；不得污染当前界面、草稿、游标或主进程pending记录。','transport_rules; identity_and_authority'),
 ('Q08','prepost_journal_failure','注入私有Main pending journal写入/rename/fsync失败，尚未发HTTP。','NOT_SENT且0POST；保留草稿/原requestID/body；不退回旧Mu或换ID自动发送。','submit_and_recovery_rules'),
 ('Q09','unknown_journal','Main已写pending，POST超时/断线或ACK落盘失败。','保留UNKNOWN和精确requestID/body/作用域；渲染端不自动POST；新的id/body不得替代未知请求。','submit_and_recovery_rules'),
 ('Q10','restart_lookup','只用fixture私有userData重启服务对象，pending=UNKNOWN；GET lookup先NOT_FOUND再FOUND。','恢复只GET原project+request_id；NOT_FOUND不清pending不解锁为新POST；FOUND须核Task归属和原请求；禁止新ID/body自动POST。','submit_and_recovery_rules'),
 ('Q11','corrupt_pending','pending文件截断、非法JSON/版本/身份、作用域不匹配、写中断余留temp；无真实用户目录。','显式存储/UNKNOWN错误并fail closed，不当无pending；不重置/覆盖成空记录；不回退旧Mu自动发送。','submit_and_recovery_rules; identity_and_authority'),
 ('Q12','manual_retry','UNKNOWN下显式用户重试相同文本/修改文本，连续双击提交。','重试若被支持只用精确原ID/body；不同body需拒绝保持未知；一次pending期间不生成第二逻辑任务/静默追加请求。','submit_and_recovery_rules'),
 ('Q13','cancel_cas','GET queued revision R→取消时已被claim，409带实际run/epoch；active epoch过期。','保留冲突/刷新GET并等待另一次明确用户动作；不能自动代换run/epoch重发cancel；CANCEL_REQUESTED不是已停止。','cancel_rules'),
 ('Q14','ipc_allowlist','renderer传绝对/相对恶意URL、任意argv/executable、bearer/authority标志、未知action/字段或坏origin。','只允许固定harness.v1动作与typed DTO，URL/认证由Main受信依赖生成；拒绝窄IPC绕过，不能传任意HTTP/进程/文件能力。','identity_and_authority; transport_rules'),
 ('Q15','credential_boundary','synthetic bearer canary只放fixture Main依赖，触发HTTP成功、401/异常、pending恢复和日志错误。','renderer返回/事件/错误/日志与pending序列化均无token/认证原文；不读真实auth目录；Main认证不出preload。','identity_and_authority'),
 ('Q16','no_fake_v2_session','选Harness Task且无旧V2 session，点击工具/成果/文件/差异/附件/恢复。','write/resume/pause/per_tool_approval/file_diff/file_list/file_artifacts/attachments均禁用或Unsupported；不造V2session触发workspace.diff，旧session与Task不混同。','capabilities_rules'),
 ('Q17','honest_capabilities','installation present、authentication LOGGED_IN，但verification三项UNVERIFIED且security_scope.enforcement_verified=false，hooks/mcp=PLATFORM_POLICY。','独立显示平台策略与未验证，不写READY/已禁hooks/MCP/模型已验证；发送仍按Host can_submit规则，不擅自把metadata升级资格或把verification改写成Host策略。','capabilities_rules; D03'),
 ('Q18','submit_gate','can_submit=false含reason codes；缺workspace/项目；附件/写模式不支持；can_submit=true但暂未资格。','阻止不支持动作并显示原因；不假造权限，不把can_submit等同LIVE_OBSERVED；READY文案需真实资格。','capabilities_rules'),
 ('Q19','ime_keyboard','compositionstart→Enter(isComposing或keyCode229)→compositionend；Shift+Enter；普通发送/停止。','IME确认不提交，Shift换行；正确可用键盘动作，无双提交；输入/停止可达。真实Electron验证另scope，不用纯函数结果声称IME通过。','V1 J03/J13; scope purpose'),
 ('Q20','draft_scope','A草稿→切B输入→A迟到发送失败/成功；发送期间用户又键入；Harness/Mu模式切换。','每上下文保草稿，新输入不被迟到结果覆盖；错误保留原文本；不同会话/模式不泄漏草稿。','V1 J03/J08/J13; identity_and_authority'),
 ('Q21','legacy_compatibility','使用原Mu/V2 fixture走选择旧session、发送、错误草稿和工具详情，不涉及新harness endpoint。','旧已工作的路径无隐式转换/回退或请求字段变化；新Task失败不能影响旧会话状态/读取diff。','scope requirements: original Mu/V2 unchanged'),
 ('Q22','unsafe_preview','assistant/tool/error text含HTML/script/javascript-link以及伪路径/超长输出。','按纯文本/安全Markdown显示，不执行HTML，不以工具正文生成URL/argv/文件授权；来源/截断可辨认。','event_payload_rules; V1 J09/J13'),
 ('Q23','terminal_unknown','Task状态UNKNOWN/BLOCKED/FAILED/CANCELLED/COMPLETED分别返回，run可null；process EOF只有LOG。','UNKNOWN是终止自动工作而非成功；无resume或自动重启；COMPLETED仅执行终态不独立接受；EOF不伪造COMPLETED。','task_status_rules; submit_and_recovery_rules'),
 ('Q24','ui_claim_limits','用户查看窄屏/双主题、历史轨迹重载和动态图谱。','320/390输入/停止可达，状态不是仅色彩；历史加载不发光；reduced-motion可用；作者build和pure结果不记真实UI通过。','V1 J13; scope verification'),
]
matrix={'schema':'researchos.productv1.workbench-independent-qa-preparation/1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'status':'PREPARED_NOT_EXECUTED','source_review_status':'WAITING_FOR_AUTHOR_FREEZE','product_acceptance_increment':0,
 'reviewer':'codex:/root/workbench_builder','author':scope['owner'],'source_base':scope['base_head'],
 'worktree':scope['worktree'],'exact_paths':scope['production_paths']+scope['test_paths'],
 'pins':{str(x):sha(x) for x in [scope_path,contract_path,d03_path]},
 'cases':[{'id':i,'area':area,'arrangement':setup,'expected':expected,'basis':basis,'status':'NOT_RUN','evidence':[]} for i,area,setup,expected,basis in rows],
 'constraints':['Do not read mutable author source/tests before explicit freeze.','No real Electron launch, Native, CLI session, login, model, old database, install or secret access in preparation.',
 'After freeze verify exact pins and stage source snapshot; independent fixtures only in a new private C scope.','Any build/test needs exact logged command, tool versions, stdout/stderr and raw exit; preserve first failures and origin attempts.',
 'Pure tests/build do not establish REAL Windows UI/model/profile enforcement qualification.','Old Core/capture scopes stay paused.'],
 'after_freeze_sequence':['Root supplies exact frozen manifest and permits QA execution.','Read actual frozen10 paths plus baseline relevant modules; verify scope pins and unchanged unexpected paths.',
 'Stage immutable QA snapshot or verify candidate read-only, preserving source hashes before/after.','Adapt independent counterexamples above to actual exported seams without modifying author tests/source.','Run locked Node pure tests and necessary source build only within authorized outputs; save all raw outcomes.',
 'Report blockers with reproduction, origin and exact source line/hash; no self-signed product acceptance.']}
HERE.mkdir(exist_ok=False)
(HERE/'matrix.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
text='''# V1 Workbench 独立 QA 准备

只读依据是已登记scope、Root冻结的Harness rev2和D03。作者未冻结，未读取候选变动源码/测试，也未运行它们。

24条反例见matrix.json，全部NOT_RUN。优先级为：UNKNOWN pending不重发、作用域/迟到隔离、int64/游标、窄IPC和凭据边界，再核queued/cancel状态与诚实能力、旧Mu兼容及草稿。真实IME/窄屏/reduced-motion和模型资格需Root另scope，不用pure/build通过替代。

注意：can_submit是Host对本次有限任务的策略结论，与metadata和verification独立。QA不能自创“verification未测必定can_submit=false”的协议；但不能因此显示READY或把平台策略写为已验证隔离。hooks/mcp须标PLATFORM_POLICY。

冻结后先校验10源pins再读源码、stage、运行独立fixture/必要build；不修改作者代码/测试，不恢复旧Core/capture、不运行真实CLI/Native/模型/旧DB。任何失败保留首次raw和来源计数。当前所有产品验收仍未验证。
'''
(HERE/'PREPARATION.md').write_text(text,encoding='utf-8')
print(json.dumps({'status':'PREPARED_NOT_EXECUTED','case_count':len(rows),'source_files_read':0,'output':str(HERE),
 'files':{x.name:sha(x) for x in HERE.iterdir()},'contract_sha256':sha(contract_path)},ensure_ascii=True))
