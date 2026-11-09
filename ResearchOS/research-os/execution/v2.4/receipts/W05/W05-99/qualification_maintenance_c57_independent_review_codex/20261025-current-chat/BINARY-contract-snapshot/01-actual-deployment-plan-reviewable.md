# 未来部署审查矩阵（非执行单）

状态NOT_IMPLEMENTED_NOT_ACCEPTED。实际目标清单尚缺，因此本文件不能当可执行部署计划；finiteblockeddecision.md是当前决策。没有执行ACL/registry/native probe/DB/API/launch/stop/Restart操作。

| 阶段 | 精确动作与输入 | 成功条件 | 失败/撤除 |
|---|---|---|---|
| PREPARED | 接受的57路径候选build/helper hash；完整入口图每条exact target file ID+hash+descriptor；原root/DB identity；另行accepted online backup manifest；管理员恢复主体 | schema/platform/token/ancestor等无UNKNOWN；恢复副本在root之外受保护且可用 | 无改动，拒绝arm |
| APPLYING | 先保护外部operation控制目录；逐目标open retain no-delete metadata；比较expected original descriptor/hash/ID；持久写before记录并flush；只写冻结精确FILE_EXECUTE或FILE_READ_DATA围栏；读回 | 每个target的读回完全匹配expected installed descriptor且普通token不能修改 | 部分成功保持APPLYING；逐条仅对current==installed且ID未变的目标恢复original；冲突不覆盖，交同operation管理员恢复，边界UNPROVEN |
| ARMED | 封存全目标applied/readback、pre witness和backup digest；禁止普通更新/新副本注册 | 全覆盖，独立接受；此状态仍未静默，旧Core可ONLINE | expiry/取消不自动unfence；受保护记录失效，管理员按原descriptor恢复；不停止旧Core |
| 用户未来FullRestart | 只有部署/backup/Source/fixture/独立接受后，另行用户明确窗口 | post uptime严格下降，LastBoot与明确完成证据相容；所有围栏跨boot存在 | 不要求用户现在重启；取消/休眠/同boot/延迟越界拒绝，无伪boot receipt |
| BOOT_OBSERVED | 先重读全目标ID/hash/ACL/祖先、fence inventory及无普通新boot启动证据；再native root lease与dispatch owner lock | 同host/SID/root/DB；完整census，无UNKNOWN/permissions gap；lease retained | 任何中断拒绝；不能以新PID快照补历史Wait |
| C_HELD | 冻结当前C计划，双journal own permit、schema24 write reservation、Host/effect/B private variant和CAS全部验证 | 全前提成立；5version精确事务；外部UNKNOWN无遗漏 | 保留journal/原证据；precommit未应用按NOT_APPLIED，已commit只recover terminal receipt |
| C_DURABLE | 精确marker+delta/census、C durable terminal、所有lease/guard仍held | 独立operation核验，不自动D/qualification | marker/状态冲突UNKNOWN；不重放、不恢复backup覆盖root |
| DISARMING | 独立撤除授权记录绑定operation/终态；仍holding root lease；目标current descriptor==installed逐一恢复original并readback | 完整恢复清单；ordinary新gate可见durable C journal | partial restore停止进一步动作，记录哪些已恢复；仍保留root lease至安全退出。进程崩溃导致lease丢失时不能保证已恢复旧入口不启动，因此boundary作废且不得继续C；保留已提交事实/失败，不以重跑修复 |
| CLOSED | 完整restore后封存consumed generation再释放lease；无自动launch | 无pending未知项；新ordinary启动仍经原产品门禁 | 离线管理恢复只能撤除基础设施阻断；C/UNKNOWN状态不被宣告成功 |

DACL操作不是多文件原子事务。partial apply在preboot不能推出无新启动；只有全部armed并经过FullRestart后才可能建current boundary。撤除只发生C已durable之后；撤除中crash不能支持持续current-quiescence或随后同permit维护。所有恢复动作留append-only记录，不删before/failed记录。

重放：同op相同plan允许status/只补终态读回，不重复DB mutation；同op不同plan拒绝；consumed op不重新arm；过期后需要新op但必须先分类旧op，不通过新目录跳过旧pending。换hash/file ID/owner/ancestor就不能restore覆盖；管理员恢复必须具体审查漂移，不能给出takeown/icacls-reset通配符。

不锁死前提：管理恢复程序与控制记录不处于被围栏阻断的目标集合，备份原descriptor在root外；已证明能在普通产品SID被拒绝时恢复。无法提供该主体/路径就不得开始APPLYING。恶意管理员、同SID任意绕过程序、VM回滚不在可信操作假设，但正常官方launch/update必须覆盖。

