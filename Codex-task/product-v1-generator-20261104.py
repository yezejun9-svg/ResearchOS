from pathlib import Path
import datetime
import hashlib
import json

TASK = Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task')
OUT = TASK / 'product-v1-plan-20261104'
SPEC = Path('D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4')
REPO = Path('D:/作品集/ResearchOS/research-os')
LANCER = Path('D:/开发工具/lancer-1.0.1/lancer-1.0.1')
PI = Path('C:/nvm4w/nodejs/node_modules/@earendil-works/pi-coding-agent')
CODEX = Path('C:/nvm4w/nodejs/node_modules/@openai/codex')
VENDOR = REPO / 'third_party/mu/packages/coding-agent'
PAUSE = REPO / 'execution/v2.4/receipts/product-shape-replan-20261104/PAUSE.json'
NOW = datetime.datetime.now(datetime.timezone.utc).isoformat()
SCHEMA = 'researchos.product-v1-plan/1'

def load(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

tasks = load(SPEC/'contracts/tasks.json')['tasks']
cases = load(SPEC/'contracts/acceptance.json')['cases']
assert len(tasks) == 22 and len(cases) == 42
assert {t['task_id'] for t in tasks} == {f'W{i:02d}' for i in range(22)}
assert {c['id'] for c in cases} == {f'C{i:02d}' for i in range(1,27)} | {f'A{i:02d}' for i in range(1,17)}
pause = load(PAUSE)
assert pause['checkpoint_revision'] == 602
assert pause['legacy_acceptance_cards_paused'] is True
CODEX_PROBE = TASK/'product-v1-codex-local-probe-01/result.json'
codex_probe = load(CODEX_PROBE)
assert codex_probe['prompts_sent'] == codex_probe['model_requests_sent'] == 0
assert codex_probe['real_task_qualified'] is False

# This is an exhaustive disposition table, not an implementation/completion ledger.
TM = {
 'W00': ('RETAIN',['J01'], '保留身份、Git脏改动、来源与失败证据保护；新V1只在Root登记的新scope施工，不恢复旧卡。'),
 'W01': ('REFRAME',['J02','J03','J10'], '将Mu/Pi唯一底座二选一改为Go Host唯一权威，先一个Codex adapter、后另一Pi adapter；多模型不当多Harness。'),
 'W02': ('RETAIN',['J02','J08','J12'], '保留自有CLI/Desktop共享Host与锁版本，按新有限用户旅程核验，不沿用空壳或build通过。'),
 'W03': ('RETAIN',['J01','J07','J08','J11'], '保留持久状态、事务/去重/CAS与单Host写入权威；不迁移旧DB、不再重造完整通用领域。'),
 'W04': ('REFRAME',['J04','J07'], '自然语言转成用户可审阅的有界coding任务与范围快照；全研究Goal影响传播后置。'),
 'W05': ('REFRAME',['J03','J05','J06','J07'], '自有CLI为薄客户端；复用真实Harness工具/会话运行，不再自造LLM/tool主循环。'),
 'W06': ('REFRAME',['J04','J05','J10','J11'], '固定串行实现、另一Harness只读评审、用户diff接受；V1没有自主多轮调度/自签接受。'),
 'W07': ('DEFER',[], 'GitHub/X/论文采集服务不进入首版有界coding闭环；未来单独来源/权限验收。'),
 'W08': ('DEFER',[], '持续研究和候选判断后置；首版只展示真实任务状态与当前候选。'),
 'W09': ('DEFER',[], '通用证据索引/检索后置；V1只读取本任务明确输入、回执、diff和交付物。'),
 'W10': ('DEFER',[], '完整实验平台后置；V1执行用户明确的有界本地检查，保留原始exit与输入hash。'),
 'W11': ('DEFER',[], 'Jev用途资格/留出集评分不进入V1；另一Harness的评审不冒充Jev或正式接受。'),
 'W12': ('REFRAME',['J04','J06','J07'], '保留停止、明确费用未知、持久失败计数和UNKNOWN拒盲重试；额度自动切换及无限连续执行后置。'),
 'W13': ('REFRAME',['J01','J03','J09','J12'], '11页后台改为默认React三栏对话工作台：项目/会话、会话输入、真实任务轨迹与成果。'),
 'W14': ('REFRAME',['J08','J10','J11'], '改为CLI/Desktop同Host任务接续与coding候选接受；不再让完整研究周期成为首个用户动作。'),
 'W15': ('DEFER',[], '研究到技能自动晋升后置；首版可引用既有经授权技能，不自动写入/晋升。'),
 'W16': ('DEFER',[], '系统自动自我迭代、canary与自更新回滚明确后置，禁止作为V1默认循环。'),
 'W17': ('REFRAME',['J01','J02','J08','J11'], '本机权限、凭据不泄漏和Host边界保留；手机监督/远程配对/正式留出集服务后置。'),
 'W18': ('REFRAME',['J13'], '先支持新V1 owned root的明确导出与新目录恢复，不声称旧DB迁移或prepared addon已被采用。'),
 'W19': ('DEFER',[], '8小时隔夜、睡眠/断电和无人持续执行后置；V1必须能安全停止和如实恢复记录。'),
 'W20': ('RETAIN',['J12','J13'], '仍交付真实Windows CLI与Desktop包，正常使用不靠开发者手动管理命令；安装/build与真实使用分层。'),
 'W21': ('REFRAME',['J07','J09','J13'], '保留任务产物/版本/回执交接；下一轮由用户启动，不自动启动飞轮。'),
}
CM = {
 'C01': ('REFRAME',['J07','J08'],'本机两端打开同一任务/会话和上下文；不承诺自动跨writer或跨Host接管。'),
 'C02': ('RETAIN',['J01','J08'],'同名路径/项目仍需稳定身份和明确授权；禁止混入其他项目资料。'),
 'C03': ('REFRAME',['J04','J09','J11'],'范围/基线改变使旧review和apply失效；不实现完整研究依赖传播。'),
 'C04': ('RETAIN',['J07','J08','J11'],'保留重复/乱序事件去重和CAS，冲突需可见且不能覆盖新改动。'),
 'C05': ('DEFER',[],'无研究候选也能完成的研究语义后置；V1任务失败/未变化仍如实保留。'),
 'C06': ('DEFER',[],'X来源覆盖与限流不属于首版coding任务。'),
 'C07': ('RETAIN',['J09','J10','J11'],'任何模型报告/评分不能覆盖失败测试、未验证证据或用户未接受。'),
 'C08': ('DEFER',[],'Jev服务故障与用途资格不是首版另一Harness评审。'),
 'C09': ('REFRAME',['J09','J10','J11'],'局部实现/评审成功不能掩盖所选任务回归；系统自身canary后置。'),
 'C10': ('RETAIN',['J04','J10','J11'],'实现者和评审不能改验收门自证；用户接受独立且绑定输入/候选。'),
 'C11': ('REFRAME',['J06','J07','J08'],'中断先对账、UNKNOWN不重发；不承诺现有运行任意时刻跨进程透明接管。'),
 'C12': ('DEFER',[],'自动canary退化回退及候选冻结不在V1；用户拒绝候选则不应用。'),
 'C13': ('REFRAME',['J04','J07'],'费用可以未知，不默认编造额度；V1一次有界任务，不承诺无限跨会话连续执行。'),
 'C14': ('REFRAME',['J04','J06'],'用户可缩小/停止本次任务，Host拒新增工作；跨并发金额预留后置。'),
 'C15': ('REFRAME',['J02','J07'],'额度/登录缺失如实阻塞对应Harness，不静默切换或重复发送已未知请求。'),
 'C16': ('RETAIN',['J04','J07'],'有界重试/无进展记录持久保留，改task/candidate名称不能清零。'),
 'C17': ('REFRAME',['J03','J07'],'状态/成果事件去重，重开可查看；系统通知和远程通知不是首版必须。'),
 'C18': ('RETAIN',['J03','J04'],'显示实际已完成/失败/未开始，未知不伪造百分比。'),
 'C19': ('DEFER',[],'转载来源去重属于后续研究索引；本任务回执按真实id/hash去重。'),
 'C20': ('RETAIN',['J09','J10','J11'],'改评分或显示规则不构成改善；验收方案改动使旧证据失效。'),
 'C21': ('REFRAME',['J09','J10'],'保留检查输入/完整输出/exit/hash及不同Harness评审，正式实验资格后置。'),
 'C22': ('DEFER',[],'正式留出集服务后置且旧权限不变；V1不读取它或派生标签。'),
 'C23': ('REFRAME',['J01','J03','J08','J09'],'11路由改为三栏和按需面板，核心操作与状态须接真实Host。'),
 'C24': ('RETAIN',['J03','J12'],'清爽双主题、响应式、键盘/IME、焦点与reduced-motion必须真实Windows UI验证。'),
 'C25': ('RETAIN',['J09','J11'],'不可信产物安全预览，版本冲突拒接受，模型文本不能变可执行HTML或路径授权。'),
 'C26': ('RETAIN',['J03','J07','J08'],'真实事件投影/断线补齐/状态一致；光线和日志不是业务状态权威。'),
 'A01': ('REFRAME',['J01','J04'],'明确输入范围/hash和owned workspace，不把所有旧规格导入设为首个任务前置。'),
 'A02': ('REFRAME',['J02','J03','J10'],'Go Host是唯一调度/权限权威；分别验证Codex/Pi能力，不沿用Mu/Pi路线二选一。'),
 'A03': ('RETAIN',['J07','J08','J11'],'事务、幂等、冲突和CAS保留；仅对新V1数据路径与用户动作重新证明。'),
 'A04': ('RETAIN',['J03','J05','J06'],'真实Harness执行、流式工具、停止及子进程收尾必须实测，不以fixture替代。'),
 'A05': ('DEFER',[],'GitHub/X/论文服务及故障探针后置。'),
 'A06': ('DEFER',[],'通用检索权限/增量/缓存资格后置。'),
 'A07': ('DEFER',[],'正式冻结实验和无法确定结论后置，不把任务测试包装成完整实验平台。'),
 'A08': ('DEFER',[],'Jev冻结留出测评后置，原留出输入/标签不读。'),
 'A09': ('DEFER',[],'资料到技能晋升后置。'),
 'A10': ('REFRAME',['J03','J08','J12'],'保留Windows Desktop真实使用；手机监督不纳入V1。'),
 'A11': ('REFRAME',['J02','J08','J11'],'本机凭据/权限边界保留；远程设备配对与撤销另行验收。'),
 'A12': ('REFRAME',['J13'],'新V1 root导出/新目录恢复；旧DB迁移失败回退仍未完成。'),
 'A13': ('REFRAME',['J04','J05','J09','J10','J11'],'首个真实有界coding任务代替完整研究周期；真实项目、真实diff、真实另一Harness评审、用户接受。'),
 'A14': ('DEFER',[],'8小时隔夜/睡眠/断电资格不作为首版功能声明，明确后置。'),
 'A15': ('REFRAME',['J12','J13'],'仍需可复现Windows包/真实用户启动与记录；V1十三旅程不冒充旧42已通过。'),
 'A16': ('DEFER',[],'系统自身自动迭代/灰度/控制面回滚后置，V1无自动自更新。'),
}
assert set(TM) == {x['task_id'] for x in tasks}
assert set(CM) == {x['id'] for x in cases}

JR = [
 ('J01','SINGLE_HARNESS','打开或选择项目，明确工作区与已有改动',
  ['Root已登记新V1代码scope；用户明确选择真实仓库；读取身份不写旧数据'],
  ['显示绝对路径/稳定项目身份、HEAD及dirty状态；同名项目不混合；原改动保持'],
  ['项目身份/HEAD/dirty快照','操作前后文件hash或diff','真实Desktop选择项目录屏/截图'], ['S01','S04']),
 ('J02','SINGLE_HARNESS','看到Harness可用性、版本与资源缺口',
  ['只读发现Codex/Pi公共manifest；运行能力探测须新登记scope；不读取或复制认证文件'],
  ['分别显示discovered、协议已测、登录未知、真实执行已测；无资源只阻塞对应adapter；费用未知明确显示'],
  ['manifest/二进制版本及hash','脱敏协议握手与能力记录','缺登录/不可用失败证据'], ['S01','S02','S07']),
 ('J03','SINGLE_HARNESS','在三栏会话输入并看到真实回复和工具过程',
  ['Codex adapter协议兼容已测；用户为一次真实调用提供有效资源；Host唯一调度'],
  ['主输入框可键盘/IME输入；流式回复和工具状态绑定同一task/run/session；右栏节点可定位原回执；历史加载不伪装实时活动'],
  ['真实Harness请求/响应/事件脱敏raw与exit','Host有序事件索引/hash','真实Windows Electron录屏与DOM/截图'], ['S02','S03','S04']),
 ('J04','SINGLE_HARNESS','把请求变成可审阅的有界实现任务',
  ['用户确定目标、允许路径、基线、验收检查、时间/步骤上限与停止规则'],
  ['清楚显示范围/输出/检查/上限；用户确认的任务绑定不可变输入hash；模型不能扩大权限或改验收'],
  ['有界任务合同与用户确认','输入/基线/检查hash','越界任务被拒原始证据'], ['S01','S03','S04']),
 ('J05','SINGLE_HARNESS','串行完成一次候选实现和检查',
  ['J04合同明确；独立owned worktree/root；单个实施Harness；显式批准的命令能力'],
  ['一次只有一个实现任务执行；修改留在候选；真实测试exit与产物可看；不会自动启动下一轮'],
  ['原始工具与进程事件','候选patch/文件hash/检查完整stdout stderr及exit','原项目未覆盖证明'], ['S03','S05']),
 ('J06','SINGLE_HARNESS','停止任务且后续队列不会自行恢复',
  ['J05真实任务处于运行或排队；Host可发当前adapter的取消动作'],
  ['立即停止新增dispatch；Pi先clear_queue再abort并核settled/current_state；子进程未证停止显示STOPPING/UNKNOWN；用户停止保持'],
  ['停止请求及排队/abort顺序raw','子进程/队列收尾证据','停止后无新增执行事件'], ['S02','S03','S06','S07']),
 ('J07','SINGLE_HARNESS','错误或重启后看见准确状态而不重复执行',
  ['本任务持久事件与输入hash存在；仅操作新owned数据root'],
  ['缺回复/断线/进程退出标UNKNOWN或BLOCKED，先对账不自动重发；失败来源/次数不重置；重开保留候选与日志'],
  ['中断前后事件水位和原始诊断','重开记录及无重复dispatch计数','明确用户resume动作与对账结果'], ['S03','S06']),
 ('J08','SINGLE_HARNESS','CLI和Desktop查看同一任务与会话',
  ['同一Go Host和新V1 root；两个薄客户端；真实本机身份/权限路径另行验证'],
  ['两端task/session/run一致；输入来源与事件可追溯；不根据client_id字符串自动给予writer接管或证明sameOS'],
  ['两端真实命令/界面录屏与Host事件关联','重复/乱序/断线反例','权限拒绝/单Host锁证据'], ['S03','S04','S06']),
 ('J09','SINGLE_HARNESS','审阅交付物、真实diff与检查结果',
  ['候选基线/输出hash和检查结果存在；文件路径在授权范围'],
  ['成果可打开预览和定位变更；不可信内容安全显示；测试失败/未测与模型完成分开；节点commit标签不得假称Git提交'],
  ['基线/候选diff、文件hash与检查raw','路径/不可信内容/冲突反例','真实Desktop成果/diff视图'], ['S05','S06']),
 ('J10','DUAL_HARNESS','由另一Harness只读评审固定候选',
  ['J09固定候选；Pi与Codex两个不同Harness协议与真实运行均分别验证；评审scope只读'],
  ['评审读取确切基线/patch/测试证据；显示Harness身份/版本；不写候选、不替代测试、不自动修复或自签接受'],
  ['第二Harness真实请求和评审产物hash','实施/评审进程与版本分离证据','只读/越权拒绝证据'], ['S07','S08']),
 ('J11','DUAL_HARNESS','用户看完diff和评审后明确接受或拒绝',
  ['J10评审完成；J09硬检查均有结果；当前原仓库仍匹配基线；用户显式操作'],
  ['只有用户的hash绑定接受才允许应用；基线/候选漂移拒绝；拒绝保留候选；模型/另一Harness的完成不等于接受；不自动commit/push'],
  ['用户接受或拒绝回执与baseline/candidate/review hashes','CAS冲突/测试失败阻止反例','应用前后diff及用户录屏'], ['S08','S09']),
 ('J12','WINDOWS_DELIVERY','普通Windows用户安装、启动并完成真实交互',
  ['已构建哈希绑定的自有CLI/Desktop包；合法依赖/字体notice；全新受控Windows用户root'],
  ['正常使用无需外部Node和手工后台管理命令；三栏清爽、键盘/IME/焦点/reduced-motion可用；安装/更新/卸载不默删项目；打包成功不算用户旅程通过'],
  ['安装包/source/bundle manifest与SHA','干净Windows安装/启动/停止/卸载记录','真实Electron任务/工具/diff流程及可用性证据'], ['S09','S10']),
 ('J13','WINDOWS_DELIVERY','导出本次任务并在新目录恢复可审阅记录',
  ['仅新V1 owned root；导出不含令牌或模型密钥；明确新目标目录；完整性校验'],
  ['任务/候选/评审/接受/失败记录可导出且hash验证；新目录恢复不自动运行任务或复活凭据；旧DB/prepared addon迁移仍Unsupported'],
  ['导出manifest/hash与敏感信息检查','新目录恢复前后inventory/hash','损坏拒绝及恢复后无执行证据'], ['S06','S10','S11']),
]
journeys = []
for jid,layer,title,pre,checks,artifacts,slices in JR:
    journeys.append({'id':jid,'layer':layer,'title':title,'status':'NOT_RUN','implementation_status':'NOT_STARTED',
        'required_mode':'REAL','execution_mode':'NOT_RUN','measurement_mode':'NOT_RUN',
        'prerequisites':pre,'observable_results':checks,'evidence_required':artifacts,'evidence':[],
        'planned_source_slices':slices,'legacy_references':[k for k,v in CM.items() if jid in v[1]],
        'supplemental_modes':['STATIC','UNIT','FIXTURE_ELECTRON'],
        'supplemental_evidence_cannot_satisfy_REAL':True})

SLICES = [
 ('S01',[],'有界V1合同、数据root与安全接点',
  ['docs/product-v1/PLAN.md','contracts/product-v1/task.schema.json','internal/host/productv1_contract.go','internal/host/productv1_contract_test.go'],
  'Root登记新scope/接口lease后定义task/run/command/event/artifact/review/acceptance IDs、稳定输入hash、状态机和新owned root；先决定与现有Host/store的薄集成，不复用未采用addon或自动迁旧库。',
  ['非法范围/空值/未知字段/状态转换拒绝','验收定义及源hash绑定','原Main/旧数据库/旧工作树不改']),
 ('S02',['S01'],'第一个Codex薄RPC适配',
  ['adapters/harness/adapter.go','adapters/harness/codex_rpc.go','adapters/harness/codex_rpc_test.go'],
  '先确认本机Codex0.166.0的实际受支持RPC/app-server握手与schema；adapter只做stdio请求/事件/错误/取消映射，未知能力fail closed。只凭包manifest不运行真实任务。',
  ['真实本地协议握手/能力版本证据','命令ACK与任务终态区分','取消/退出/坏帧/重复/oversize/背压测试']),
 ('S03',['S02'],'Go Host唯一权威的单任务纵切',
  ['internal/host/productv1_runtime.go','internal/host/productv1_journal.go','internal/host/productv1_runtime_test.go'],
  'Host持有任务许可、单执行锁、session映射、进程生命周期与持久事件；复用Harness原生工具，不再自建模型工具循环。一次任务结束停在候选态。',
  ['单Harness真实有界任务与真实工具事件','命令幂等/非零失败/UNKNOWN对账','权限/路径/参数越界拒绝']),
 ('S04',['S03'],'薄CLI和React三栏真实输入',
  ['apps/cli/productv1.go','apps/cli/productv1_test.go','apps/web/src/productv1/workbench.jsx','apps/web/src/productv1/use-host-session.js','apps/web/src/productv1/workbench.css'],
  'CLI和Desktop都调用相同Host；左项目/最近会话、中对话和底部输入、右任务/工具/成果；设置折叠。最先让用户可输入和查看真实工具过程。',
  ['CLI/Desktop同task/session/run','失败保草稿、IME/键盘和窄屏','真实Electron发送/事件/错误流程']),
 ('S05',['S03','S04'],'隔离候选实现、检查和成果diff',
  ['internal/host/productv1_candidate.go','internal/host/productv1_candidate_test.go','apps/web/src/productv1/artifacts.jsx','apps/web/src/productv1/diff-view.jsx'],
  '用户指定范围后在owned隔离工作区实现一次；固定基线/候选内容与测试证据；不覆盖原工作树、不自动commit/push。',
  ['真实有限实现和真实检查完整输出','dirty原仓库保护','diff/路径/不可信内容预览反例']),
 ('S06',['S05'],'停止、重连和真实事件可视化',
  ['internal/host/productv1_reconcile.go','internal/host/productv1_reconcile_test.go','apps/web/src/productv1/activity-projection.js','apps/web/src/productv1/light-layer-adapter.js','apps/web/src/productv1/activity-projection.test.js'],
  '先实现持久状态/停止/补齐，再局部适配MIT LightUI。事件id去重、先挂DOM再emit、历史不重放、取消/会话切换清理、未知不用假进度。',
  ['真实停止及无新增dispatch','中断/重复事件/重开不盲重发','历史hydration/缺anchor/reduced-motion/跨会话隔离']),
 ('S07',['S06'],'第二个Pi0.99.2薄RPC适配',
  ['adapters/harness/pi_rpc.go','adapters/harness/pi_rpc_test.go'],
  '按已安装0.99.2 docs+dist验证而非LancerSDK1.4或vendor0.87；prompt disposition处理started/queued/handled，handled无run不等待settled；取消先clear_queue再abort。',
  ['真实独立Pi握手与有界任务','handled/queued/started与终态回归','清队列/取消/断线及版本不匹配拒绝']),
 ('S08',['S05','S07'],'另一Harness只读评审',
  ['internal/host/productv1_review.go','internal/host/productv1_review_test.go','apps/web/src/productv1/review-panel.jsx'],
  '默认Codex实现→Pi评审；评审固定patch/检查/raw/hash并独立记录Harness身份，只读且不触发自动修复。反向组合后续单独验证。',
  ['真实不同Harness评审','拒绝同Harness冒充双Harness','只读权限、证据漂移、失败测试不洗白']),
 ('S09',['S08'],'用户diff接受与CAS应用',
  ['internal/host/productv1_accept.go','internal/host/productv1_accept_test.go','apps/web/src/productv1/accept-controls.jsx'],
  '用户显式接受绑定task/baseline/candidate/review/check hashes；当前基线不符拒绝；应用有备份/失败收尾；拒绝保留候选。',
  ['真实用户接受/拒绝','候选或基线变化及检查失败拒绝','原改动保留、无自动commit/push/下一轮']),
 ('S10',['S09'],'Windows自包含开发包与真实用户交付',
  ['apps/desktop/build-development.py','apps/desktop/main/main.js','apps/desktop/main/preload.js','tests/ui/productv1-workbench-fixture.cjs'],
  '保留原bundle另建candidate；完整source-bound重建后先dryrun，再Root登记真实Windows隔离交付测试；不得仅替renderer或伪称安装。',
  ['source/binary/dependency/license manifest','干净用户实际安装启动/IME/任务/diff/停止','卸载与数据保护']),
 ('S11',['S06','S10'],'V1记录导出与新目录恢复',
  ['internal/host/productv1_export.go','internal/host/productv1_export_test.go','apps/cli/productv1_export.go','apps/web/src/productv1/export-controls.jsx'],
  '仅新V1数据root导出/完整性校验/新目录恢复；不导出凭据，不自动恢复执行。旧SQLite迁移、Native prepared addon生产采用仍阻塞后置。',
  ['导出/恢复真实inventory和内容hash','损坏/重复/秘密材料拒绝','恢复无自动执行且旧数据不变']),
]
plan_slices = []
for sid,deps,title,paths,behavior,verify in SLICES:
    plan_slices.append({'id':sid,'depends_on':deps,'title':title,'status':'NOT_STARTED','verification_status':'NOT_RUN',
        'proposed_paths':paths,'paths_are_not_a_write_lease':True,'behavior':behavior,'verification':verify,
        'acceptance_journeys':[j['id'] for j in journeys if sid in j['planned_source_slices']],
        'source_owner':'ROOT_TO_REGISTER','independent_reviewer':'ROOT_TO_ASSIGN'})

sources = []
def evidence_file(group,base,rel,lines=None,claim=None):
    p = base/rel
    assert p.is_file(), str(p)
    entry={'group':group,'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size,'observed_utc':NOW,
           'method':'READ_EXISTING_BYTES_ONLY','execution_performed':False}
    if lines: entry['relevant_lines']=lines
    if claim: entry['visible_fact']=claim
    sources.append(entry)
    return p

for rel in ['contracts/tasks.json','contracts/acceptance.json','contracts/execution.plan.json']:
    evidence_file('legacy_frozen_spec',SPEC,rel)
evidence_file('pause',PAUSE.parent,PAUSE.name,claim='CP602 retains old cards, failures and source worktrees paused; this plan does not resume them.')
evidence_file('root_metadata_probe',CODEX_PROBE.parent,CODEX_PROBE.name,claim='Root observed version/help/login status only; zero prompts/model requests, no persisted raw auth output, not real-task qualification.')
manifest_reads = [
 ('installed_codex',CODEX,'package.json'),('installed_pi',PI,'package.json'),('vendor_pi',VENDOR,'package.json'),
 ('lancer',LANCER,'package.json'),('lancer',LANCER,'apps/desktop/package.json'),
 ('lancer',LANCER,'packages/pi-sdk-driver/package.json'),('lancer',LANCER,'packages/light-ui/package.json')]
manifests={}
for group,base,rel in manifest_reads:
    p=evidence_file(group,base,rel); v=load(p)
    manifests[group+':'+rel]={'name':v['name'],'version':v['version'],'license':v.get('license'),'sha256':sha(p),'path':str(p)}
for rel,lines in [('docs/cli.md',[48]),('docs/rpc.md',[60]),('docs/rpc-commands.md',[94]),('docs/json.md',[45]),('dist/modes/rpc/rpc-mode.js',[298,327,331,345,474])]:
    evidence_file('installed_pi_protocol',PI,rel,lines)
for rel in ['docs/rpc.md','docs/rpc-commands.md','docs/cli.md']:
    evidence_file('vendor_reference_only',VENDOR,rel)
for rel,lines in [
 ('AGENTS.md',None),('LICENSE',None),('NOTICE',None),('README.md',[9,18,106,158]),
 ('pnpm-lock.yaml',[121,421,434]),('PUBLIC-SOURCE-MANIFEST.json',None),
 ('packages/light-ui/LICENSE',None),('packages/light-ui/NOTICE',None),('packages/light-ui/src/light-layer.ts',[45,62,116,184,187,209]),
 ('packages/light-ui/src/index.ts',[1]),('packages/light-ui/src/running-border.css',None),
 ('packages/session-driver/src/types.ts',[177,216,237,257,375]),
 ('packages/pi-sdk-driver/src/pi-sdk-driver.ts',[37,48,81]),
 ('packages/pi-sdk-driver/src/session-supervisor.ts',[973,1586,2294,2350,2359]),
 ('apps/desktop/electron/application/app-store.ts',[297,1265,1303,2930]),
 ('apps/desktop/src/features/conversation/lancer-process/live-model.tsx',[45,82]),
 ('apps/desktop/src/features/conversation/lancer-process/live-emissions.ts',[13,51]),
 ('apps/desktop/src/features/conversation/lancer-process/process-types.ts',[64]),
 ('apps/desktop/src/features/conversation/lancer-process/relay-tree.ts',[253]),
 ('apps/desktop/electron/orchestration/branch-return.ts',[12,27]),
 ('docs/platform-validation.md',None),('docs/third-party-dependencies.md',None)]:
    evidence_file('lancer_static',LANCER,rel,lines)
for rel,lines in [('internal/host/host.go',[112,149,215]),('apps/cli/cli_native.go',None),
 ('apps/desktop/main/main.js',None),('apps/web/src/workbench.jsx',None),('internal/domain/store.go',[54,66])]:
    evidence_file('researchos_existing_source',REPO,rel,lines)
assert manifests['installed_codex:package.json']['version']=='0.166.0'
assert manifests['installed_pi:package.json']['version']=='0.99.2'
assert manifests['vendor_pi:package.json']['version']=='0.87.1'
assert manifests['lancer:package.json']['version']=='1.0.1'
assert manifests['lancer:packages/light-ui/package.json']['version']=='0.1.0'
lancer_driver=load(LANCER/'packages/pi-sdk-driver/package.json')
assert lancer_driver['dependencies']['@earendil-works/pi-coding-agent']=='^1.4.0'
assert "'@earendil-works/pi-coding-agent@1.4.0'" in (LANCER/'pnpm-lock.yaml').read_text(encoding='utf-8')

evidence = {
 'schema':SCHEMA,'created_utc':NOW,'status':'STATIC_INVENTORY_ONLY','runtime_verification_status':'NOT_RUN',
 'new_implementation_status':'NOT_STARTED','product_acceptance_status':'NOT_RUN','sources':sources,'manifests':manifests,
 'version_matrix':[
  {'component':'installed Codex','version':'0.166.0','availability':'MANIFEST_PRESENT_VERSION_AND_EXEC_HELP_OBSERVED','protocol':'exec flags statically advertised; RPC/app-server compatibility NOT_RUN','login':'OBSERVED_LOGGED_IN_CHATGPT_STATUS_ONLY','real_execution':'NOT_RUN','quota':'UNVERIFIED','cancel_resume':'UNVERIFIED','windows_ui':'NOT_RUN'},
  {'component':'installed Pi CLI','version':'0.99.2','availability':'MANIFEST_AND_RPC_SOURCE_PRESENT_DISCOVERED','protocol':'Static docs/dist inspected; handshake NOT_RUN','login':'UNKNOWN_NOT_INSPECTED','real_execution':'NOT_RUN','windows_ui':'NOT_RUN'},
  {'component':'ResearchOS vendor Pi/Mu subtree','version':'0.87.1','availability':'SOURCE_REFERENCE_ONLY','protocol':'Must not be substituted for installed0.99.2 protocol','login':'NOT_INSPECTED','real_execution':'NOT_RUN','windows_ui':'NOT_RUN'},
  {'component':'Lancer Desktop','version':'1.0.1','availability':'LOCAL_SOURCE_ARCHIVE','protocol':'Pi SDK-based; not a proven multi-Harness router','login':'NOT_INSPECTED','real_execution':'NOT_RUN','windows_ui':'NOT_RUN'},
  {'component':'Lancer Pi SDK dependency','version':'declared^1.4.0 / lock1.4.0','availability':'DECLARED_AND_LOCKED_NOT_INSTALLED_VERIFIED','protocol':'SDK AgentSession; not installed Pi0.99.2 RPC','login':'NOT_INSPECTED','real_execution':'NOT_RUN','windows_ui':'NOT_RUN'},
  {'component':'Lancer LightUI','version':'0.1.0','availability':'MIT_SOURCE_PRESENT_NO_RUNTIME_DEPENDENCIES','protocol':'SVG/DOM visual primitive only','login':'NOT_APPLICABLE','real_execution':'NOT_APPLICABLE','windows_ui':'NOT_RUN'}],
 'static_conclusions':[
  'Lancer sends through PiSdkDriver and upstream AgentSession.prompt. Multiple providers/models do not establish multiple CLI Harnesses.',
  'Lancer handoff-workflow changes model/activeStep; prepare-workflow creates draft, not an automatic stage executor.',
  'Lancer task graph commit/gate labels are not Git commits or ResearchOS acceptance.',
  'LightUI and live-emission hygiene are appropriate local reuse candidates; retain MIT/NOTICE. Do not fork accounts/auth/session ownership.',
  'Pi prompt command success covers disposition, not task completion; handled may produce no run. Clear queues before abort for a full stop.',
  'No installed CLI is qualified by this inventory; Root version/help/login-status probe sent zero prompts/model requests. No login action, real task/UI, build, install or native behavior test was performed.'],
 'codex_root_metadata_probe':{'result_path':str(CODEX_PROBE),'sha256':sha(CODEX_PROBE),
  'executable_sha256':codex_probe['executable_sha256'],'version_exit':0,'exec_help_exit':0,'login_status_exit':0,
  'auth_status':'OBSERVED_LOGGED_IN','auth_mode':'chatgpt','prompts_sent':0,'model_requests_sent':0,
  'credential_files_read_by_controller':0,'raw_auth_output_persisted':False,'real_task_qualified':False,
  'advertised_flags':['--json','--ephemeral','--sandbox','--skip-git-repo-check','--output-schema','--ignore-user-config'],
  'limitations':['Observed credential status does not prove model availability, quota, cancel, resume or task correctness.','This planning author only read the already completed sanitized report; did not rerun its commands.']},
 'archive_manifest_declaration':{k:v for k,v in load(LANCER/'PUBLIC-SOURCE-MANIFEST.json').items() if k in ('revision','candidate','exportedAt','note')},
 'legacy_pause':{'checkpoint':602,'main_head':pause['main_head'],'aggregate_records_at_pause':pause['historical_aggregate_diagnostic_records'],
   'legacy_formal_accepted':pause['legacy_formal_accepted'],'legacy_formal_required':42,'counter_reset':False,
   'pending_branch_diagnostics':pause['pending_branch_diagnostic_aggregation'],'old_unknown_qualifications_preserved':True},
 'limitations':['This package contains planning plus static source hashes only.','A source manifest version is not binary/runtime compatibility proof.',
   'No credentials, authentication directories, private model configuration, old database or holdout inputs/labels were read.',
   'Proposed source paths are a planning manifest, not permission to edit shared files or assign migration numbers.']}

mapping = {'schema':SCHEMA,'created_utc':NOW,'mapping_status':'PLANNED_NOT_IMPLEMENTED','source_package_version':'2.4.0',
 'source_hashes':{n:sha(SPEC/n) for n in ['contracts/tasks.json','contracts/acceptance.json','contracts/execution.plan.json']},
 'policy':{'old_contracts_edited':False,'old_PASS_inherited':False,'old_failure_records_preserved':True,'failure_counter_reset':False,
  'old_formal_acceptance_completed':False,'legacy_cards_paused':True,'new_v1_acceptance_is_separate':True,
  'deferred_does_not_mean_accepted':True,'retain_does_not_mean_implemented':True},
 'parent_tasks':[], 'formal_cases':[]}
for t in tasks:
    disposition,ids,reason=TM[t['task_id']]
    mapping['parent_tasks'].append({'legacy_id':t['task_id'],'legacy_title':t['title'],'disposition':disposition,
      'v1_journeys':ids,'reason':reason,'legacy_acceptance_ids':t['acceptance_ids'],'legacy_owned_acceptance_ids':t['owned_acceptance_ids'],
      'legacy_definition_status':t['status'],'completion_transfer':'NONE','v1_implementation_status':'NOT_STARTED','v1_verification_status':'NOT_RUN'})
for c in cases:
    disposition,ids,reason=CM[c['id']]
    mapping['formal_cases'].append({'legacy_id':c['id'],'legacy_title':c['title'],'disposition':disposition,'v1_journeys':ids,'reason':reason,
      'legacy_mode':c['mode'],'legacy_gate_scope':c['gate_scope'],'legacy_final_owner_task':c['final_owner_task'],
      'legacy_definition_status':c['status'],'legacy_assertion_ids':[a['id'] for a in c['assertions']],
      'legacy_evidence_requirements':c['evidence_required'],'completion_transfer':'NONE','v1_implementation_status':'NOT_STARTED','v1_verification_status':'NOT_RUN'})
mapping['coverage']={'parent_tasks':22,'formal_cases':42,'missing_parent_ids':[],'missing_case_ids':[],
 'task_dispositions':{d:sum(x['disposition']==d for x in mapping['parent_tasks']) for d in ['RETAIN','REFRAME','DEFER']},
 'case_dispositions':{d:sum(x['disposition']==d for x in mapping['formal_cases']) for d in ['RETAIN','REFRAME','DEFER']}}

acceptance = {'schema':SCHEMA,'created_utc':NOW,'status':'NOT_RUN','implementation_status':'NOT_STARTED','required_journey_count':13,
 'layers':{'SINGLE_HARNESS':{'journeys':[j['id'] for j in journeys if j['layer']=='SINGLE_HARNESS'],'status':'NOT_RUN'},
           'DUAL_HARNESS':{'journeys':['J10','J11'],'status':'NOT_RUN'},'WINDOWS_DELIVERY':{'journeys':['J12','J13'],'status':'NOT_RUN'}},
 'release_rule':'All13 journeys need current-source REAL evidence and independent review; user acceptance is a separate explicit action. No new PASS by fixture, build or old receipt inheritance.',
 'first_milestone_rule':'Single-Harness milestone may demonstrate J01-J09 but must not claim dual-Harness review or completed V1 release.',
 'journeys':journeys,'evidence_binding':['source_revision_and_dirty_manifest','host_build_hash','adapter_and_runtime_versions',
 'task_id','run_id','session_id','input_hash','baseline_hash','candidate_hash','checks_hash','review_hash','user_action_receipt'],
 'status_rules':['ACK is not completion.','Harness/model completion is not acceptance.','UNKNOWN/BLOCKED/NOT_RUN remain distinct.',
 'Missing resources block only their dependent layer.','User STOP persists; no autonomous retry/review/fix loop.','Do not print credentials or model private chain-of-thought.']}

plan = {'schema':SCHEMA,'created_utc':NOW,'status':'PLANNED_NOT_IMPLEMENTED','implementation_status':'NOT_STARTED','verification_status':'NOT_RUN',
 'authority':'GO_HOST_SINGLE_OUTER_AUTHORITY','first_harness':'CODEX_PROTOCOL_ELIGIBILITY_FIRST','second_harness':'PI_0_99_2_READONLY_REVIEW',
 'first_harness_selection_is_not_qualification':True,'default_flow':['user_scopes_task','one_harness_implements_once','fixed_candidate_and_checks',
 'different_harness_reviews_readonly','user_inspects_diff','user_accepts_or_rejects'],
 'autonomous_self_iteration':False,'automatic_commit_push':False,
 'construction_prerequisites':['Root reviews/copies this package into project continuation records.',
   'Root registers one exact isolated source scope/worktree and owner before source writes.',
   'Old22/42 cards and paused candidate worktrees remain preserved; no old model scope replay.',
   'Shared contracts/GoHost/control/schema changes stay serial under Root; proposed paths require actual inspection before scope registration.'],
 'implementation_policy':{'max_active_source_owners':2,'one_implementer_for_each_path':True,'independent_review_required':True,
   'keep_all_failure_attempts':True,'same_origin_automatic_retries':2,'no_progress_iteration_limit':3,'counter_reset':False},
 'slices':plan_slices,'completion_not_claimed':True,
 'open_decisions_before_implementation':[{'id':'D01','choice':'Codex first adapter protocol must be pinned to real0.166.0 local schema/handshake; if unsupported, BLOCKED with evidence and explicit route decision, not silent fallback.'},
  {'id':'D02','choice':'Root must choose the smallest versioned V1 durable record extension in the single Host/store. Default new owned data root; no second scheduler and no oldDB migration. Exact schema paths/number not assigned by this plan.'},
  {'id':'D03','choice':'Permission modes exposed to UI are capabilities verified for each actual Harness, not caller booleans or model claims.'}],
 'non_goals':['Automatic self improvement/canary/skills promotion','Phone/remote supervision','Full research harvest/index/experiment/Jev suite',
 'Overnight unattended execution','Old database migration/preparedNative addon adoption','Parallel implementer fleet','Model private chain-of-thought display']}

md = '''# ResearchOS 产品 V1：可输入、可看见、可审阅的本地 AI 工作台

状态：**规划完成待Root归档；产品未实现、未验证。** 本包只在C任务目录落盘，不修改Main、旧工作树、旧数据库、旧22/42验收或失败台账。Root归档后按新scope直接实施，不再请求用户重复批准。

## 产品结果

用户打开自己的项目，在一个干净的桌面端输入有界coding任务，看到真实回复、工具调用、检查和成果。一个Harness串行实现一次，固定候选后交给另一个Harness只读评审；用户看到diff和证据后决定接受或拒绝。接受只对当前hash对应的候选有效。V1不自动进入自我迭代、不自动commit/push、不让模型完成或另一模型认可变成产品接受。

首个开发里程碑只打通单Harness。完整V1还需双Harness和Windows交付两层证据，不能用第一个里程碑宣称全部完成。

## 默认页面

默认使用现有React技术栈和三栏信息结构，不把用户带回11页配置后台：

- 左栏：项目、最近情况、会话、当前任务；项目路径与状态可辨认。
- 中栏：会话画布、Markdown回复、可展开工具过程；底部始终有可输入的CLI风格composer、附件/范围、发送/停止。
- 右栏：有界任务步骤、当前工具/检查、候选成果和diff、评审与用户接受状态。细节按需展开，原始回执可查。

视觉采用干净留白、深绿/暖白与深色主题，克制的黑客感；不堆原始日志，也不把装饰光线当进度。窄屏折叠边栏但输入与停止始终可达。必须验证IME、键盘、焦点、文字可读性和reduced-motion。

## 唯一执行权威与复用边界

Go Host是权限、任务上限、单执行锁、会话身份、持久事件、候选和用户接受的唯一外层权威。CLI/Desktop都是薄客户端。Codex/Pi adapter只做实际受支持协议的进程/stdio/请求/事件/错误/取消映射；Harness内的模型与工具循环继续由Harness负责，不在Go里重造第二套。

默认先验证本机Codex0.166.0的RPC/app-server协议资格，再打通单任务；第二阶段适配Pi0.99.2做只读评审。两者的版本、登录、协议和真实执行分别记录。若Codex协议资格不满足，仅阻塞该支路并报告；不静默换实现、不复活旧Mu/Codex资格会话。普通shell终端可作为按需面板，不能成为唯一用户交互或任意命令授权绕道。

本机已安装Pi0.99.2、ResearchOS vendor0.87.1、Lancer SDK声明/锁1.4.0是三套不同版本。Lancer多模型Pi SDK并不等于多个CLI Harness；不能将其事件接口直接套到0.99.2 RPC。

## 一次有限闭环

1. 用户选择项目，Host记录HEAD、dirty、输入、允许路径、检查和上限。
2. 用户确认有界任务。Host只启动一个实施Harness，修改进入owned隔离候选，不覆盖旧工作树。
3. 接受命令ACK、流式消息、工具事件、检查exit分别入账。未知费用/状态如实显示；ACK不是完成。
4. 实施终止后固定baseline/candidate/check hashes。真实检查失败保留，不被模型总结洗白。
5. 另一Harness只读评审该固定候选与证据，输出带Harness版本和输入hash的评审产物；不自动修复或自签。
6. 用户看diff/检查/评审后接受或拒绝。应用前CAS核当前基线与候选；漂移拒绝，拒绝则保留候选。随后停止，下一轮由用户启动。

## 停止、失败与恢复

停止先关闭Host新增dispatch；Pi的完全停止需clear_queue后abort，并核对终态/实际队列。prompt的started/queued/handled只是处理结果，handled可能根本没有run，不能一律等agent_settled。其他Harness按自己固定版本合同核验。子进程未证停止只能显示STOPPING/UNKNOWN。

断线或重启后先对账，UNKNOWN不自动重发。用户STOP持续有效。失败来源、输入、候选和次数持久保留，不因新名字/新会话/新Goal清零；同源自动重试最多2次，连续3轮无进展停对应支路。资源缺口只阻塞相关adapter/验收层。所有旧UNKNOWN和已消费模型scope保持，不重放。

## Lancer可复用范围

优先局部引入MIT LightUI0.1.0：`light-layer.ts`、`geometry.ts`、`svg.ts`、`running-border.css`，保留LICENSE/NOTICE。它无运行时依赖，不需Lancer账号、Electron或模型SDK。参考`live-emissions.ts`的历史基线抑制、会话切换清理，以及timeline viewport和工具折叠布局。

借用`SessionDriverEvent`的会话/工具事件形状作为映射参考，另由Host补稳定事件ID、任务/运行/输入hash及真实接受依据。不得直接把Lancer的window.piApp、账号、~/.pi/agent、会话owner或整个DesktopAppStore移成新主控。任务图中的commit是显示事件，不必是Git提交；branch-return的worker-reported只是报告，不是独立接受。LightUI发光只由真实离散事件驱动，历史加载不发光、缺anchor不接邻居，不显示模型私有思维链。

## 验收与旧规格

`acceptance.json`固定13条用户旅程：J01–J09单Harness、J10–J11双Harness、J12–J13 Windows交付。每条目前NOT_RUN，REAL证据需绑定实际source/build/adapter版本、task/run/session、输入/基线/候选/检查/评审hash。静态检查、单元、fixture Electron、真实Harness、真实Windows UI、安装分别报告；fixture/build成功不能替代REAL。

`legacy_mapping.json`完整读取并逐项映射外部v2.4的22父任务及42正式用例为保留、改写成V1用户结果或后置。映射不是修改旧合同，也不是给旧门签PASS。旧PASS不自动继承；旧失败/重试/UNKNOWN不删不清，旧全量ResearchOS目标仍未完成。V1只是用户新授权的首版范围。

## 实施顺序与续跑

`plan.json`只有11个可审阅的小切片：S01合同/新root→S02 Codex协议→S03单Host运行→S04 CLI/三栏→S05候选diff→S06停止/恢复/LightUI→S07 Pi→S08另一Harness评审→S09用户接受→S10 Windows包→S11记录导出恢复。路径为建议，不是写入lease；Root登记实际worktree、source pins和共享文件owner后才施工。

每片实施、窄测、独立复核、保存检查点再续跑。每次只证明本层实际结果。新V1 root默认不碰旧DB；schema扩展由Root在单Host/store中定案，不创建第二调度器、私自编号migration或采用prepared addon。当前旧施工保持CP602暂停；这份规划不恢复它。

## 首版明确后置

研究源采集/通用检索/正式实验/Jev留出评测、资料到技能晋升、系统自动自我迭代/灰度、手机远程监督、隔夜无人执行、旧DB迁移及Native prepared addon生产采用、并行实施者集群。它们保留历史映射和证据，不能靠缩小首版宣称已接受。

## 当前证据界限

本规划作者只读公共manifest、源码、规格和Root已完成的脱敏探测报告。Root已实际观测Codex0.166.0版本、exec help及logged_in/chatgpt凭据状态，均exit0、0prompt/0模型请求、未保存原始认证输出；没有进行登录动作。这不证明模型、额度、取消/恢复或真实任务资格。Pi运行完全未测。未构建安装、未验证真实UI。Lancer文档明确macOS为主验目标，Windows本轮只有配置/打包路径而无native接受；不能照搬支持结论。详见`evidence.json`的逐文件hash与版本/未验证矩阵。
'''

# Only this C planning directory is writable by this controller.
assert OUT.parent.resolve() == TASK.resolve()
OUT.mkdir(exist_ok=False)
def write_json(name,data):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n')
with (OUT/'PLAN.md').open('x',encoding='utf-8',newline='\n') as f: f.write(md)
write_json('acceptance.json',acceptance)
write_json('legacy_mapping.json',mapping)
write_json('evidence.json',evidence)
write_json('plan.json',plan)

# Planning validation only; never product acceptance or a legacy status update.
assert len(load(OUT/'acceptance.json')['journeys'])==13
assert len(load(OUT/'legacy_mapping.json')['parent_tasks'])==22
assert len(load(OUT/'legacy_mapping.json')['formal_cases'])==42
seen=set()
for s in plan_slices:
    assert set(s['depends_on'])<=seen
    seen.add(s['id'])
assert all(j['status']=='NOT_RUN' and not j['evidence'] for j in journeys)
assert len(list(OUT.iterdir()))==5
print(json.dumps({'status':'PLAN_FILES_WRITTEN_PRODUCT_NOT_IMPLEMENTED','output':str(OUT),
 'counts':{'journeys':13,'legacy_parents':22,'legacy_cases':42,'slices':11,'static_sources':len(sources)},
 'files':{p.name:{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.iterdir())},
 'mapping_coverage':mapping['coverage'],'no_product_tests_or_runtime_executed':True},ensure_ascii=True))
