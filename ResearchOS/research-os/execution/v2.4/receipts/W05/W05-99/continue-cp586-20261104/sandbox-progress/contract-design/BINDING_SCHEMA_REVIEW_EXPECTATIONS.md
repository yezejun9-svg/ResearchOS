# Binding schema prototype — review expectations

C-only设计边界；不分配产品DB schema/迁移编号，不连接旧库，不D写，不注册checker或开放LIVE。对应Root新C-only DDL+fresh SQLite fixture施工，冻结后才独立运行必要fixture。

## 字段与索引

最低SQL可定位字段：binding_schema/version、project、goal_id、task_id、approval_id及其issuer namespace、intent_key、owner_principal/root/host、task_contract_hash、goal_contract_hash、binding_body、binding_hash。正文另固定原method/client/command/request、Session/Workspace/ref hash、profile/policy/suite/approved-plan、Requirement/input refs、origin_problem/candidate/NoProgress与创建writer epoch/revision。

原Owner来自确认token，root来自currentAuthorityRoot，Host来自可信ConfigurationAuthority，不能从模型/CLI/locator获得。创建时未产生Run，不填假run_id或lease_epoch；后续真实TaskRun、current lease/epoch/profile/purpose/native证明属于域/Host consumer。

跨principal约束：PRIMARY KEY(project,task_id)，UNIQUE(project,goal_id)，UNIQUE(project,intent_key)。approval一次只绑一Goal：若approval ID是可信全局UUID可全局UNIQUE；否则声明真正issuer namespace并对(namespace,approval_id)唯一，不能用换principal/project规避同一批准。不要把principal放进这些唯一键。SQL只能约束给定的stable intent key，不能发现故意改名的同一业务；Host必须从批准的原始业务anchor/canonical refs和原lineage计算稳定key，拒绝v1重新命名/newGoal/newApproval/newArtifact ID洗NoProgress。

## SQL保证与非保证

| SQL/fresh fixture可证明 | 必须由后续域/Host证明 |
| --- | --- |
| NOT NULL、版本/格式、列与body字段一致（若DDL实现） | 该Owner/root/Host是否真实且当前获准 |
| 跨principal唯一、approval/intent不可重复消费 | approval签发与消费是否合法、caller是否允许创建该业务 |
| 全列UPDATE/DELETE拒绝、冲突不覆盖 | 当前RBAC、writer/lease/epoch、资格/purpose与native admission |
| transaction rollback不留半条绑定 | Task/Goal双合同及公开对象/input refs真实冻结且当前 |
| fresh backup/restore完整schema+row读回 | 原origin/candidate/NoProgress连续性、业务正确或接受 |

binding_hash格式和SQL里一串相同字符串不是正确哈希或认证。canonical body/hash、strict版本/字段/duplicate-key解码、实际上下文与公开对象必须由consumer复算。caller不能通过command ID选择host operation；原V2 replay operation由服务固定v2:前缀，但这也不能让prototype consumer自称实现了Host认证。

## 必要反例

- 不同principal但同project/task、goal、approval或intent，插入都不得绕唯一性。相同stable intent换newGoal/newTask/newApproval名字仍拒绝，而非重建零失败记录。
- 所有UPDATE（包括no-op）与DELETE拒绝；INSERT OR REPLACE、ON CONFLICT DO UPDATE/DO NOTHING与INSERT OR IGNORE不能静默改变或误报一次新绑定成功。必须验证原row逐字节保留。REPLACE测试包含recursive_triggers=0与1；不要仅依赖DELETE trigger，必要时加BEFORE INSERT冲突guard。
- JSON CHECK中的缺失字段/NULL不能因SQLite三值逻辑通过：用明确IS/COALESCE或strict consumer拒绝；JSON null/array、duplicate keys、unknown/case-alias字段、非有限数、列body错配、哈希错配/旧版本均有明确拒绝。
- 用显式BEGIN插入后ROLLBACK，行数/唯一claim恢复；失败插入不吞异常，也不留下partial approval consumption。重放先读既有准确绑定并拒新Goal/回原引用，不以upsert替代不可变历史。
- SQLite backup到全新C fixture后检查表/索引/全部约束和触发器及row；缺一个trigger/index、表同名但shape不同、tampered body/hash都必须被schema/consumer完整性检查拒绝。不能只验证表存在或行数。

fresh fixture可用假的ExpectedContext证明匹配/拒绝算法，但该context是测试输入，不是可信Host实现。报告应写INTEGRITY_FIXTURE/SCHEMA_PROTOTYPE，不写AUTHENTICATED/BUSINESS_PASS/ACCEPTED。普通Goal503、SDK sole output、pending audit/Task+Goal factories、REPORT到source bundle的消费链均仍未实施。