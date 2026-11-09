# 阶段1追加：合法 OS 祖先与业务 token 的验证边界

状态 `FIXED_CONTRACT_CONSULTATION_NOT_SOURCE_ACCEPTANCE`。既有58项断言及三个报告/seal不变。本轮只读Root040固定快照和既定历史metadata，并查阅微软primary资料；没有读取原ACL/原进程，没有测试、部署、Source接受或要求用户批准现在部署。

**结论：应修正访问判断语义，不能以永久拒绝既定平台或改整盘ACL满足合同。** 管理state的严格两主体策略不能机械套到所有OS祖先；也不能反向将BA或OS路径全部豁免。

## 固定证据

- Root `C57-ancestor-contract-observation-cp540.json`及其snapshot：`040-boot-ancestor-mutable-source.snapshot.txt` SHA256 `9a07a6e386a2da3e2717385ade81ce253a49ccae6f76b551c7703780c328e8b4`，49963 bytes。它是过去mutable内容的固定观察，不是待接受commit。
- 历史 `file-ancestor-metadata.json` SHA256 `f4c58e80940d0dc81ce9c0bac70a1131030238c27cfe7e9347e749ac33d71cc5`。记录明确不是retained native identity/fence证明，不能作为本轮真实当前ACL。
- 已采用 `qualification_boot_supplement_independent_design_review_codex/20261015-current-chat/design-review.md` SHA256 `3965106935192d75a8bff39d5c21edd3d98e63417f1ed19067c8a36d2e2f290c`，25–37行明确：当时business token是Medium/BA deny-only；D根AU有效0x1301bf无DELETE_CHILD/WRITE_DAC/WRITE_OWNER；不改D:/、C:/、C:/Users合法ACL；SYSTEM/TrustedInstaller owner保留。选中作品集/home/.codex等祖先另有明确未来授权范围，业务data/DB/WAL不能机械封写。

Root040 snapshot:578只允许ManagementSID/SYSTEM owner，585–605没有INHERIT_ONLY或实际token筛选，把其他所有危险ALLOW均当作business可用权限。因此会在合法D根的`(A;OICIIO;GA;;;BA)`或`(A;;FA;;;BA)`处拒绝；前者不是当前对象有效ACE，后者是否授予business必须结合token属性判断。

## 足够且不扩大机制的边界

1. **分清对象职责，仍逐对象核验。** exact管理state/record、受围栏target及选中需保护产品祖先，按各自已采用管理/恢复合同验证。合法OS祖先保留其SYSTEM/TrustedInstaller等已采用可信系统管理主体及原ACL；核验其native identity、当前SD及选中child边缘是否可被非可信主体替换。不能把“保护管理state只准两SID”变成“整条Windows目录只准两SID”，也不能按`C:`/`D:`名字直接跳过验证。
2. **ACE要按对象和flags解释。** `INHERIT_ONLY_ACE`不作用于所在对象；`INHERITED_ACE`不是“不生效”的同义词。跳过本对象的IO判断后，仍要检查每个实际选中child继承后的有效SD。保留owner、继承/保护控制及dense ACE，不通过删除合法IO ACE来让检查通过。[Microsoft ACE_HEADER](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-ace_header)
3. **实际业务token是权限判断输入。** native查询并绑定真正business token的user、SID_AND_ATTRIBUTES、owner、integrity/elevation、restricted状态及相关privileges；enabled group可参与ALLOW/DENY，deny-only只参与DENY。BA在Medium受限token中deny-only时，其ALLOW不赋权；同SID换成enabled/elevated token必须重新判断、不得沿用先前结论。普通disabled-but-enableable与deny-only不同，不能误当永远不可启用。跨boot应重采当前token并验证同business SID及规定token类别，不要求跨boot TokenId相等，也不能把旧TokenId当现在持有的token。[Microsoft SID attributes](https://learn.microsoft.com/en-us/windows/win32/secauthz/sid-attributes-in-an-access-token)、[TOKEN_GROUPS](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-token_groups)
4. **复用原生访问语义，避免自造完整ACL解释器。** 在既有六文件scope内，可用真实业务token的合法impersonation副本和同handle取得的SD调用AccessCheck；不是新增fence机制。使用对象类型正确的generic mapping，检查API成功与AccessStatus两个结果，不能以API返回非零当allow。逐项检查危险权，或取得完整GrantedAccess后判断任何危险位：把DELETE_CHILD|WRITE_DAC|WRITE_OWNER合并请求被拒，不代表每一项均被拒。JSON group列表或helper自身管理token不能替代business token。真实token不可用时，保留该actual分支未证明，同时完成源码和自有token夹具。[Microsoft AccessCheck](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck)
5. **按命名空间边缘检查风险，不能只查当前用户。** 对选中child检查其DELETE/owner改权/内容或reparse替换入口，同时检查parent的DELETE_CHILD；其他非可信普通主体的宽泛写权仍须按采用合同覆盖。BA/SYSTEM/TrustedInstaller的合法可信系统管理能力不等于普通business拥有该权；但未知custom trustee、无法闭合主体集合或unsupported ACE不能静默忽略。必要时对无法证明的精确计划拒绝，不把全平台永久拒绝当完成。AccessCheck只回答指定token对指定SD的判断，不证明“所有其他人均无权”。[Microsoft access-check order](https://learn.microsoft.com/en-us/windows/win32/secauthz/how-dacls-control-access-to-an-object)
6. **D根例外只能来自固定语义，不能放宽child。** 已采用D根AU0x1301bf含DELETE但无DELETE_CHILD/WRITE_DAC/WRITE_OWNER；合法volume根不是可被当普通child移动的产品祖先。应把该volume-root类型及原生identity作为明确条件，在测试中覆盖；对非volume-root目录仍检查DELETE。AU在根上创建无关siblings不直接等于能替换已存在且独立保护的选中child；child自身有效ACL、祖先rename/reparse以及data必要创建权限仍须逐项验证。父SD不能代替子文件本身的访问控制。[Microsoft file security](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights)

这些语义只修复采用机制的验证边界。它们不授权修改OS根、shared祖先或原数据权限；不要求新服务、账号或另一套策略系统。管理恢复与third-party descriptor保护仍按前补充保持，不因为OS兼容修正而放宽。

## 新增必要正反断言（原58项不动）

| ID | 正反输入 | 断言与资源 |
|---|---|---|
| OA01 | 固定D根完整SD + 经native证明的Medium/BA deny-only业务token；同SD + BA enabled/elevated token | 前者不能仅因BA FA或IO GA被误拒；后者不能套用deny-only结论，须按合同拒绝不合business类别或检出危险权。纯SD fixture只测语义，真实token native正证另列。 |
| OA02 | 本对象IO危险ACE；同ACE去IO；子对象继承后为effective | IO对本对象不生效；去IO/child生效后重新判断并捕获危险权；不能把全部inherited ACE跳过。 |
| OA03 | SYSTEM/TrustedInstaller合法OS owner；同SD改business owner/custom owner | 固定可信OS owner不触发“必须改为manager”；业务implicit改权或未知owner不能因OS路径标签被放过。无需改真实OS ACL。 |
| OA04 | 只允许WRITE_DAC而拒DELETE_CHILD/WRITE_OWNER；危险权组合请求返回deny | 检查仍识别WRITE_DAC危险；避免AND请求结果被误读为所有危险权均无。 |
| OA05 | child拒DELETE但parent允许DELETE_CHILD；child可DELETE而parent拒DELETE_CHILD；两者均受控 | 前两项拒绝；最后一项才可继续验证其他条件。对自有fixture可做原生负例。 |
| OA06 | 缺group属性/伪造deny-only JSON、helper管理token替代business、unknown custom group、相关privilege/token类别漂移 | 全部拒绝或明确UNAVAILABLE，不构造可提交authority。真实业务token与copy的持有/绑定需native证据。 |
| OA07 | D根AU0x1301bf + 合法volume-root身份；相同mask用于可移动产品祖先；去掉DELETE_CHILD保护或增WRITE_DAC | 固定OS根不因合法ADMIN/IO策略误拒；可移动祖先或新增危险权拒绝；不能一律忽略root或一律禁写data。 |
| OA08 | 合法OS根不修改 + 选中产品祖先/target正确保护 +业务SQLite/WAL/lease；完整反例增加custom普通主体危险权 | 同一政策下namespace负例与真实业务数据正例同时成立，descriptor原样保持；distinctSID/fullRestart/actual部署资源缺失只标对应未证明。 |

本机自有fixture可覆盖SD/ACE解释、当前token复制/查询、AccessCheck以及自有namespace/SQLite动作，但本轮未执行。不能通过伪造一个业务SID或SD字符串获得原业务token的证明。真实不同SID恢复、完整既定平台部署和FullRestart仍须后续资源与原授权边界；现在不请求部署批准。

## 捕获与失败

022–024只读命令native exit0；新非零0，累计reviewer非零仍2。023工具显示曾截断长源码，但持久stdout.raw完整保留，024补取有界行号；这不是源码接受或缺失raw。两次官方页面读取的请求及工具原结果保存在WEB-ancestor-semantics-primary-01/02.json；初次发现性web search仅保留工具会话结果，结论只使用已单独保存的官方页面。025单独finalizer保留自身捕获。候选测试0、原ACL/进程访问0、formal增量0。完成后等Root最终freeze。
