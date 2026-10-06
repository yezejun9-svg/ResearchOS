from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent
def load(name):return json.loads((OUT/name).read_text(encoding='utf-8'))
a=load('inventory-audit.json');m=load('reuse-matrix.json');b=load('reuse-subset-binding.json')
refs=[]
for c in m['cases']:
 for p in c['acceptance_refs']:
  if p not in refs:refs.append(p)
ids={p:f'E{i+1:02}' for i,p in enumerate(refs)}
lines=['# 最终验收索引版本复用审计', '', '**READ_ONLY_VERSION_REUSE_AUDIT；需要补充定向版本证据，不签最终接受。**', '',
f'固定源码：`{a["target_source"]}`；读取 main：`{a["sampled_head"]}`。两者差异只有 execution 元数据/归档证据，未出现额外产品源码修改。', '',
'42 个 case 当前为 34 PASS、6 NOT_RUN、1 BLOCKED、1 PARTIAL；本审计不改任何历史状态。建议 8 项作为有范围限制的复用候选，26 项补充定向版本证据，按 9 组共享边界合并处理；这不是要求重跑 26 套完整测试。8 项未通过项仍按原规格保留。', '',
f'34 项都有 case envelope source inventory（16–345 路径）。全部声明源码 hash 能对应其记录的 Git 源码字节；LF/CRLF 两种表示已明确区分。{len(a["external_acceptance_bindings"])} 个外部接受引用均存在，其中所有已声明 hash 均匹配；{len(a["command_verifications"])} 个 command verification 的回执 hash 均匹配。C20 外部接受在 ledger 中为字符串引用，没有独立声明 SHA256，本审计只记录实际值，不补造绑定。', '',
'每份历史 broad inventory 有 10–69 个路径变化；这些清单含共享服务、测试脚本和无关模块，数量不等于行为失效数。`inventory-audit.json` 保留逐文件旧/新 Git blob、声明 hash、原始/换行表示 hash 与全部变化；`reuse-matrix.json` 给出逐 case 的直接模块/共享边界/新增或未列入历史清单的路径。模式是人工审查范围，不能冒充完整调用图；全部依赖闭包完整性统一标为 UNKNOWN，不能因此自动撤销历史 PASS。', '',
'## 已有证据可以复用的具体范围', '',
'| Case | 复用依据 | 当前边界 |',
'| --- | --- | --- |',
'| C03、C04 | D04 独立影响传播/权限反例；main9cebc53 原始日志实际通过两项 | 5 文件比较中 changes.go 只有 serverArtifact→serverArtifactMode(FIXTURE) 提取；其余4文件相同。新增 LIVE helper 不改变旧调用参数。共享 intent/research 新路径另行检查。 |',
'| A01 | import.go、A01 所在测试、spec manifest、go.mod/go.sum 5 文件相同 | 只复用导入/规格限定语义；旧16文件清单不是全依赖闭包。 |',
'| C09 | control76b 原始日志中 TestW16C09 和3项断言 PASS；16个相关文件与最终源相同 | 同次 package 因另一个 no-gain setup 失败而 FAIL，该失败保留；不能把单 case PASS 写成整包 PASS。 |',
'| C21、A07 | S2 consumer 与 I2 再次通过 W10NativePair；25个选定 evaluator/experiment/sandbox 文件与 I2 源相同 | 复用原冻结语义矩阵及已有兼容复验；不覆盖失败的外层 native SOURCE 传输或 LIVE 资格。 |',
'| C22 | S2 consumer-tool-binding 原始日志实际通过；30个 protectedstore/C22/qualification/auth/sandbox 文件相同 | 同用户 fixture 结论，不升级为当前安装服务资格；不重跑已中止 S2 adversarial。 |',
'| A09 | D04 独立 TestW15SourceConflictFormalResolution 回归7断言；12文件比较仅上述 FIXTURE helper 提取不同 | 技能原生命周期证据保留，不把新增研究/规划路径算入旧 case。 |', '',
'逐字节结果和实际日志事件在 `reuse-subset-binding.json`。这些是 root 可审查的复用建议，未把缺失的完整依赖 inventory 补写成 PASS。', '',
'## 最小后续复验队列', '',
'| 组 | 影响 case | 最小动作与复用边界 |',
'| --- | --- | --- |',
'| R01 | C01、C02 | 当前 context materialization/授权与 C02 隔离共享矩阵；C01 复用既有模型输入输出，做本地解析/引用重算。Git 漂移本身不要求再调用供应商。 |',
'| R02 | C05、C06、A05 | 仅原 no-adoption 与两个 X 场景的 API/关闭/游标检查，加 C06 受影响界面。A05 适配器生产字节未变，复用真实供应商原始响应；当前 sources.go 的去重、正文有效性、游标/manifest 接入做离线绑定复验。 |',
'| R03 | C07、C08、A08 | 公共 fixture 硬门/弃权/缺失/注入边界；A08 只核对已经接受的安全聚合与当前 import/policy/ref 及 FAILED/ADVISORY/NONE，不读取私有标签、不重做评测。 |',
'| R04 | C10、C12、C20 | 等当前 control admission 真正冻结后，只检查受影响 legacy selector 与各原断言。control 无增益证据不等于 C20 双 rubric 完整例。涉及 native/private 的前置由 root 单独界定，不能执行旧 helper 或已禁反例。 |',
'| R05 | C11、C13、C14、C15、C16 | 按 resources.py GROUPS 合并去重，重点 budget_scopes、effect、retention、checkpoint 的改动；现有 coordinator 正常恢复与 I2 进度证据只能覆盖对应子项。原生 crash 分支另行限定，不复活 S2 adversarial。 |',
'| R06 | C17、C18、C23、C24、C25 | 原通知去重/交叉引用、4/6→4/9 计数与旧事件；补最新 UI core 未执行的状态/键盘焦点/预览项目。复用15项已完成功能检查及 resources320 修复，避免全页面全尺寸重拍。 |',
'| R07 | C19、A06 | 原来源区分/依赖失效及当前 context 引用；未变的本地 adapter、原生根身份/junction 历史证据可保留，不因 Git HEAD 再跑整组 Windows 文件系统边界。 |',
'| R08 | A02、A03 | 当前普通调度拥有权、重复派发、HTTP revision/事务/验收绑定。保持已选路线证据和已完成正常 coordinator/readiness 修复，不把 build 当行为测试，不重试已终止反例。 |',
'| R09 | A12 | 最终 schema20 公共合成数据的备份→干净隔离恢复→对账/继续任务；继承91项13→20升级断言和不变alias边界。原受保护 authority 的实际激活仍不在范围内。 |', '',
'具体测试名/命令入口及每项理由记录在 `reuse-matrix.json` 的 minimal_next_check；这里没有执行这些建议。应先冻结后续 admission 变更，再只更新受影响组，不能把 f510491 的建议无条件继承到未来源码。', '',
'## 重要的证据边界', '',
'- W13 原接受记录执行版本为 main69509c2，但 envelope inventory 标记 frontend 分支 be8f6a7；两者都保留，并列出差异，不能只凭版本名判失败。后续 I1 的 browser core 报告有15项前置检查通过，但整体 FAIL 在资源页320宽度；后续仅该视口 PASS。原始 native zoom、键盘或未执行后半段不得据此提升。',
'- I2 root integration 是源码字节核对和 build；native SOURCE binding 原始失败保留。离线 pair/monitor 子检查不能冒充这条链已通。',
'- W18 schema20 升级报告是有界机制接受；不能自动把历史 A12 或 W18 全阶段变成当前正式资格。',
'- command_verifications 记录的 registry/执行源大多早于当前版本；回执 hash 一致只证明证据完整。变化过的 wrapper/selector 应在对应组执行时绑定当前真实命令，不要全量供应商/私有/原生重跑。',
'- 本审计不访问私有 payload、不启动进程或服务、不执行测试、不改 canonical/spec/receipt；脚本只读取 Git/公开证据并写本目录。', '',
'## 42 项逐项索引', '',
'“候选复用”不是新 PASS；“定向复验”不撤销历史 PASS。模式列为历史接受模式，空值时括号记录原合同要求。', '',
'| Case | 现有状态 | 模式 | 执行源 | 接受引用 | 版本建议 |',
'| --- | --- | --- | --- | --- | --- |']
for c in m['cases']:
 state=c['reuse_assessment'];label='候选复用' if state.startswith('REUSE_') else '保留未通过' if state.startswith('OPEN_') else '定向复验'
 if 'LOCAL_BINDING' in state:label='仅本地绑定复验'
 mode=c['accepted_mode'] or '('+str(c['required_mode'])+')'
 lines.append('| '+ ' | '.join([c['case'],c['historical_status'],mode,(c['accepted_revision'] or '—')[:12],','.join(ids[x] for x in c['acceptance_refs']) or '—',label])+' |')
lines+=['','## 接受引用','']+[f'- {ids[p]}：`{p}`' for p in refs]
lines+=['','## 后续证据引用','']+[f'- {key}：`{d["ref"]}`；{d["scope"]}' for key,d in m['deltas'].items()]
(OUT/'review.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print('review_sha256',manifest['review.md']);print('files',len(manifest))
