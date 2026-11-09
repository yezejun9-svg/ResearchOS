# CP517 diagnostic / gap ledger

Query limit12；本轮使用6组（其中G01为已保守计入的输入intake，G06为产物静态封存），无扩展一般架构/初始化搜索。三份Microsoft页面是G05同一官方查询组。所有产物仅ownE；Source/testcode/当前DB/实际OS探针/API/key/model/fence/restart/launch/stop/deploy均未操作。

| 组 | 输入与目的 | 结果 |
|---|---|---|
| 初始intake | 读取项目AGENTS和CP517精确scope | shell exit0；原始tool记录有完整输出。该次未先写磁盘recipe，见G00-intake-record.json，保留偏差不补称预记录 |
| G01 | scope及九个输入hash；bounded decision/map/C scope/B final | 全部hash匹配，shell0；recipe在shell请求预先明确但独立磁盘command在执行后保存，不称事前落盘 |
| G02 | C architecture/B report/cp513 contract定位 | shell0；RESUME字段筛选因数字51匹配过宽，含无关快照字段，完整原始保存；未追加这些无关方向查询，后续G03仅精确指向 |
| G03 | CP511 adopted constraints和B report | shell0；取C51指针与兼容边界 |
| G04 | C51 scope、B75 git show私有consumer、Main startup | shell0；git raw明确NATIVE_GIT_EXIT=0；result.json native_exit_code由于PowerShell子scope变量未传出为null，保留原文件，不伪造native结果 |
| G05 | Microsoft file ACL / CreateFileW / ACL modification三官方页 | web成功；第一次用长shell字面量封存raw失败，process creation OS206，无native进程exit；第二次apply_patch封存成功。没有重做查询 |
| G06 | 已读输入hash复验，C51+6唯一集合与JSON结构、own输出封存 | 结果见G06-result.json；是静态产物完整性检查，不是Source/native测试 |

G00/G01未预先磁盘封recipe是流程偏差；原始shell/tool请求保留实际完整命令，未删改历史。G02输出在工具呈现截断但fullraw磁盘未截断；G03/04按精确对象补读。

本次新增本地诊断事件：G05原始写盘首次OS206失败一次；G04 native出口字段捕获缺失一次；G02筛选过宽一次；G00/G01事前recipe落盘缺失一次共同流程偏差。未重置任何已有产品或施工失败计数；这些只记本轮诊断，不当作业务失败/正式结果。

缺口分类：
- 可另行只读采集：完整launch注册/argv/专属文件、native ID/ACL/祖先、token/build/可用备份接口事实。精确位置和最小recipe见minimal-resource-package.md。
- 机制适用性：每条官方入口是否确有可冻结产品专属必经文件；可信管理/恢复主体可否建立，不能由更多hash自动证明。
- Source后首次产生：native权限/旧入口阻断、partial apply恢复、跨boot与permit测试；不是Source前必须先有的证据。
- actual前资源：真实可用一致性在线备份、真实全入口部署/读回独立接受；用户FullRestart只在这些完成后询问。
- 并行依赖：B75未接受，STOP/B ACL helper审查疑点不当已接受原语；见native-helper-prerequisite-note.md。
- unchanged：原Wait不可补回、F01 Host仅窄分类、外部UNKNOWN阻塞、现有STOP证明类、旧raw/ACK/cost/counters、formal0。

范围遵循：未创建额外worktree、未改Main/共享状态/归档原证据、未执行测试、未向用户提问Restart。Root仍需独立设计review，作者结果只支持有限决策。

